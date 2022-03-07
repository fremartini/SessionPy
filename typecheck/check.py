import ast
from os import getcwd
import sys
from ast import *
from pydoc import locate
from debug import *
from lib import *
from functools import reduce
from environment import Environment
import copy

from immutable_list import ImmutableList


def ch_to_mod_dir(mod_name: str):
    """
    Localises module given as string in any subdirectory recursively, and changes to this.
    Raises exception if module cannot be located.
    """
    target_dir = None
    for cur_dir, _, files in os.walk('.'):
        if mod_name in files:
            target_dir = cur_dir
            break
    if not target_dir:
        raise ModuleNotFoundError(f"imported module {mod_name} couldn't be located in any subdirectories")
    os.chdir(target_dir)


class TypeChecker(NodeVisitor):

    def __init__(self, tree, ignore_imports=False) -> None:
        self.ignore_imports = ignore_imports
        self.environments: ImmutableList[Environment] = ImmutableList().add(Environment())
        self.in_functions: ImmutableList[FunctionDef] = ImmutableList()
        self.in_classes: ImmutableList[ClassDef] = ImmutableList()
        self.visit(tree)

    def visit_Module(self, node: Module) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        self.in_functions = self.in_functions.add(node)

        expected_return_type: type = self.get_return_type(node)
        parameter_types: ImmutableList[Tuple[str, type]] = ImmutableList.of_list(self.visit(node.args))
        parameter_types = parameter_types.map(lambda tp: tp[1])
        parameter_types = parameter_types.add(expected_return_type)

        if self.in_classes.len() == 0:
            self.bind_func(node.name, parameter_types.items())
        else:
            c = self.in_classes.last().name
            env = {node.name: parameter_types}
            self.bind_class(c, env)

        self.dup()

        args = self.visit(node.args)
        for (v, t) in args:
            self.bind_var(v, t)

        for stmt in node.body:
            self.visit(stmt)

        self.pop()
        self.in_functions = self.in_functions.tail()

    def visit_Compare(self, node: Compare) -> None:
        left = self.lookup_or_self(self.visit(node.left))
        right = self.lookup_or_self(self.visit(node.comparators[0]))

        fail_if_cannot_cast(left, right, f"{left} did not equal {right}")

    def visit_Match(self, node: ast.Match) -> None:
        subj = self.visit(node.subject)
        for case in node.cases:
            self.dup()
            case: ast.match_case = case
            p = self.visit(case.pattern)

            self.bind_var(p, self.lookup_or_self(subj))
            if case.guard:
                self.visit(case.guard)

            for s in case.body:
                self.visit(s)
            self.pop()

    def visit_MatchAs(self, node: ast.MatchAs) -> Union[str, None]:
        return node.name if node.name else None

    def visit_arguments(self, node: arguments) -> List[Tuple[str, type]]:
        arguments: ImmutableList[type] = ImmutableList()
        for arg in node.args:
            arguments = arguments.add(self.visit_arg(arg))
        return arguments.items()

    def visit_arg(self, node: arg) -> Tuple[str, type]:
        match node:
            case node if node.annotation:
                ann: Typ = self.visit(node.annotation)
                return node.arg, ann
            case _:
                return node.arg, Any

    def visit_Name(self, node: Name) -> str:
        debug_print('visit_Name', dump(node))
        opt = locate(node.id)
        opt_lower = locate(node.id.lower())
        if not opt and opt_lower:  # special case when from typing
            return to_typing(opt_lower)
        return opt or node.id

    def visit_Attribute(self, node: Attribute) -> Any:
        ... # TODO: Implement

    def visit_Assign(self, node: Assign) -> None:
        # FIXME: handle case where node.targets > 1
        debug_print('visit_Assign', dump(node))
        assert (len(node.targets) == 1)
        target: str = self.visit(node.targets[0])
        value = self.visit(node.value)
        self.bind_var(target, value)

    def visit_Tuple(self, node: Tuple) -> None:
        debug_print('visit_Tuple', dump(node))
        assert (node.elts)
        elems = [self.visit(el) for el in node.elts]
        res = pack_type(Tuple, elems)
        return res

    def visit_List(self, node: List) -> None:
        debug_print('visit_List', dump(node))
        if node.elts:
            list_types: List[Typ] = [self.visit(el) for el in node.elts]
            res = reduce(union, list_types)
            return res
        else:
            return Any

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        debug_print('visit_AnnAssign', dump(node))
        target: str = self.visit(node.target)
        name_or_type = self.visit(node.annotation)
        rhs_type = self.visit(node.value)
        if is_type(name_or_type):
            self.bind_var(target, union(rhs_type, name_or_type))
        else:
            ann_type: Type = locate(name_or_type)
            assert (type(ann_type) == type)
            rhs_type: Type = self.visit(node.value)
            fail_if(not ann_type == rhs_type, f'annotated type {ann_type} does not match inferred type {rhs_type}')
            self.bind_var(target, ann_type)

    def visit_BinOp(self, node: BinOp) -> type:
        match node.left:
            case left if isinstance(left, Name):
                l = self.lookup(self.visit(left))
            case left:
                l = self.visit(left)

        match node.right:
            case right if isinstance(right, Name):
                r = self.lookup(self.visit(right))
            case right:
                r = self.visit(right)
        return union(l, r)

    def visit_Constant(self, node: Constant) -> type:
        return type(node.value)

    def compare_function_arguments_and_parameters(self, func_name, arguments: ImmutableList, parameters: ImmutableList):
        fail_if(not len(arguments) == len(parameters),
                f'function {func_name} expected {len(arguments)} arguments got {len(parameters)}')
        for actual_type, expected_type in zip(arguments.items(), parameters.items()):
            if isinstance(expected_type, str):  # alias
                expected_type = self.lookup(expected_type)

            types_differ: bool = expected_type != actual_type
            can_upcast: bool = can_upcast_to(actual_type, expected_type)
            fail_if(types_differ and not can_upcast,
                    f'function {func_name} expected {arguments}, got {parameters}')

    def get_argument_types(self, args: List[expr]) -> ImmutableList:
        types = ImmutableList()
        for arg in args:
            match arg:
                case arg if isinstance(arg, Name):
                    types = types.add(self.lookup(self.visit(arg)))
                case _:
                    types = types.add(self.visit(arg))
        return types

    def visit_Call(self, node: Call) -> Typ:
        debug_print('visit_Call', dump(node))
        func = self.visit(node.func)

        def _class_def():
            cl = f"class_{func}"
            self.bind_var(func, cl)
            return cl

        def _call():
            builtin = locate(func)
            if builtin:
                if type(builtin) == type:
                    return builtin
                else:
                    return type(builtin)

            func_name: str = self.visit(node.func)
            arguments: ImmutableList = self.get_argument_types(node.args)
            function_signature = ImmutableList.of_list(self.lookup(func_name))
            parameters = function_signature.tail()

            self.compare_function_arguments_and_parameters(func_name, arguments, parameters)

            return_type: Typ = function_signature.last()
            return return_type

        def _method():
            attr: expr = node.func
            print('HERE')
            self.print_envs()
            method = self.visit(attr.value)
            class_object = self.lookup(method)
            class_methods = self.lookup(class_object)  # {func1 : [Any -> Any], func2: ...}
            method_type = class_methods[attr.attr]  # [Any -> Any]
            return_type = method_type.last()  # get return type
            method_type = method_type.discard_last()  # remove return type
            method_type = method_type.tail()  # class object, remove 'self'
            arguments: ImmutableList = self.get_argument_types(node.args)

            self.compare_function_arguments_and_parameters(attr.attr, arguments, method_type)

            return return_type

        match node:
            case _ if isinstance(func, BuiltinFunctionType):
                return BuiltinFunctionType
            case _ if func == range:
                # TODO: (Johan) BIG HACK, investigate how to extract type information from built-ins
                return int
            case _ if isinstance(node.func, Attribute):
                return _method()
            case _ if self.lookup(func) == ClassDef:
                return _class_def()
            case _:
                return _call()

    def visit_While(self, node: While) -> Any:
        debug_print('visit_While', dump(node))
        self.visit(node.test)
        for stmt in node.body:
            self.visit(stmt)

    def visit_For(self, node: For) -> Any:
        target = self.visit(node.target)
        ite = self.visit(node.iter)
        self.bind_var(target, ite)
        for stmt in node.body:
            self.visit(stmt)

    def visit_Dict(self, node: Dict) -> Tuple[Typ, Typ]:
        debug_print('visit_Dict', dump(node))
        key_typ = reduce(union, ((self.visit(k)) for k in node.keys)) if node.keys else Any
        val_typ = reduce(union, ((self.visit(v)) for v in node.values)) if node.values else Any
        res = Tuple[key_typ, val_typ]
        return res

    def visit_Subscript(self, node: Subscript) -> Any:
        debug_print('visit_Subscript', dump(node))
        opt_typ = self.visit(node.slice)
        return opt_typ

    def visit_Return(self, node: Return) -> Type:
        match node:
            case _ if isinstance(node.value, Name):
                return_type = self.lookup(self.visit(node.value))
            case _:
                return_type = self.visit(node.value)

        return self.compare_type_to_latest_func_return_type(return_type)

    def visit_ClassDef(self, node: ClassDef) -> None:
        self.in_classes = self.in_classes.add(node)
        self.bind_var(node.name, ClassDef)
        
        for stmt in node.body:
            self.visit(stmt)

        self.in_classes = self.in_classes.tail()

    
    # def visit_ImportFrom(self, node: ImportFrom) -> Any:
    #     if self.ignore_imports:
    #         return
    #     mod_name = f'{node.module}.py'
    #     if mod_name in sys.builtin_module_names:
    #         return
    #     ch_to_mod_dir(mod_name)
    #     typed_file : TypeChecker = typecheck_file(mod_name, True)
    #     merging_env = typed_file.get_latest_scope()
    #     import_names : Set[str] = {alias.name for alias in node.names}
    #     for env_typ in merging_env.environment.keys():
    #         for k in import_names:
    #             if k not in merging_env[env_typ]:
    #                 del merging_env[env_typ][k]
    #     items = self.environments.items()
    #     print('items', items)
    #     current_items = self.environments.items()[0] | merging_env
    #     self.environments = ImmutableList.of_list([current_items])

    def visit_Import(self, node: Import) -> Any:
        if self.ignore_imports:
            return
        for module in node.names:
            module_name = module.name
            if module_name in sys.builtin_module_names:
                continue
            mod_name = f'{module_name}.py'
            ch_to_mod_dir(mod_name)
            typed_file = typecheck_file(mod_name, ignore_imports=True)
            env = typed_file.get_latest_scope()
            self.get_latest_scope().bind_import(module_name, env)

    
    def compare_type_to_latest_func_return_type(self, return_type: Typ):
        expected_return_type = self.get_current_function_return_type()
        fail_if_cannot_cast(return_type, expected_return_type,
                            f'return type {return_type} did not match {expected_return_type}')
        return return_type

    def get_return_type(self, node: FunctionDef):
        return self.visit(node.returns) if node.returns else Any

    def get_current_function_return_type(self):
        current_function: FunctionDef = self.in_functions.last()
        return self.get_return_type(current_function)

    def dup(self) -> None:
        prev_env = copy.deepcopy(self.get_latest_scope())
        self.environments = self.environments.add(prev_env)

    def pop(self) -> None:
        self.environments = self.environments.discard_last()

    def get_latest_scope(self) -> Environment:
        return self.environments.last()

    def in_latest_env(self, f : FunctionType, *args):
        env : Environment = self.get_latest_scope()
        env.f(*args)

    # HACK SECTION

    def lookup_class(self, c : str) -> dict[str, Typ]:
        return self.get_latest_scope().lookup_class(c)

    def lookup_var(self, v : str) -> Typ:
        return self.get_latest_scope().lookup_var(v)

    def lookup_func(self, f : str) -> Typ:
        return self.get_latest_scope().lookup_func(f)

    def lookup_import(self, f : str) -> dict[str, Typ]:
        return self.get_latest_scope().lookup_import(f)

    def lookup_or_default(self, k : str) -> Union[Typ, dict[str, Typ], str]:
        return self.get_latest_scope().lookup_or_default(k)
    
    def bind_class(self, cl: str, typ: Dict[str, Typ]) -> None:
        self.get_latest_scope().bind_class(cl, typ)

    def bind_var(self, var: str, typ: Typ) -> None:
        self.get_latest_scope().bind_var(var, typ)

    def bind_func(self, f : str, typ: Typ):
        self.get_latest_scope().bind_func(f, typ)

    def bind_import(self, f : str, env: Environment):
        self.get_latest_scope().bind_import(f, env)

    def lookup(self, key : str) -> Typ:
        return self.get_latest_scope().lookup(key)

    def lookup_or_self(self, k):
        return self.lookup_or_default(k)

    # HACK SECTION END

    def print_envs(self) -> None:
        print("[")
        for env in self.environments.items():
            print(f'  {env}')
        print("]")

def typecheck_file(file, ignore_imports=False) -> TypeChecker:
    src = read_src_from_file(file)
    tree = parse(src)
    return TypeChecker(tree, ignore_imports)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expected 1 argument, got 0')
        sys.exit()
    else:
        typecheck_file(sys.argv[1])

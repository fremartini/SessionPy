import ast
import copy
import sys
from ast import *
from functools import reduce
from pydoc import locate

from debug import *
from environment import Environment
from immutable_list import ImmutableList
from lib import *
from statemachine import SMBuilder


class TypeChecker(NodeVisitor):

    def __init__(self, tree, inside_class=False) -> None:
        self.inside_class = inside_class
        self.environments: ImmutableList[Environment] = ImmutableList().add(Environment())
        self.in_functions: ImmutableList[FunctionDef] = ImmutableList()
        self.visit(tree)

    def visit_FunctionDef(self, node: FunctionDef) -> Typ:
        self.in_functions = self.in_functions.add(node)

        expected_return_type: type = self.get_return_type(node)
        params = self.visit(node.args)
        if self.inside_class:
            fail_if(params[0][0] != 'self', "a class function must have self as first parameter")
            params = params[1:]
        function_type: ImmutableList[Tuple[str, type]] = \
            ImmutableList.of_list(params) \
                .map(lambda tp: tp[1]) \
                .add(expected_return_type)

        self.get_latest_scope().bind_func(node.name, function_type.items())
        self.dup()
        for (v, t) in params:
            self.bind_var(v, t)

        for stm in node.body:
            self.visit(stm)

        self.pop()

        self.in_functions = self.in_functions.tail()

        return function_type.items()

    def visit_Compare(self, node: Compare) -> None:
        left = self.lookup_or_self(self.visit(node.left))
        right = self.lookup_or_self(self.visit(node.comparators[0]))

        fail_if_cannot_cast(left, right, f"{left} did not equal {right}")

    def visit_AugAssign(self, node: AugAssign) -> None:
        debug_print('visit_AugAssign', dump(node))
        target = self.lookup_or_self(self.visit(node.target))
        value = self.lookup_or_self(self.visit(node.value))

        fail_if_cannot_cast(target, value, f"{target} is not compatible with {value}")

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

    def visit_Name(self, node: Name) -> Tuple[str, Typ] | Typ:
        debug_print('visit_Name', dump(node))
        opt = locate(node.id)
        opt_lower = locate(node.id.lower())
        if not opt and opt_lower:
            return to_typing(opt_lower)
        return opt or self.get_latest_scope().lookup_var_or_default(node.id,
                                                                    self.get_latest_scope().lookup_func_or_default(
                                                                        node.id, node.id))

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

    def visit_Attribute(self, node: Attribute) -> Typ:
        debug_print('attribute', dump(node))
        value = self.visit(node.value)  # A
        attr = node.attr  # square
        env = self.get_latest_scope().lookup_nested(value)
        return env.lookup_func(attr)

    def visit_Assign(self, node: Assign) -> None:
        # FIXME: handle case where node.targets > 1
        debug_print('visit_Assign', dump(node))
        assert (len(node.targets) == 1)

        if self.is_session_type(node.value):
            graph = SMBuilder(node.value).build()
        else:
            target = self.visit(node.targets[0])
            value = self.visit(node.value)

            self.bind_var(target, value)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        debug_print('visit_AnnAssign', dump(node))

        if self.is_session_type(node.value):
            graph = SMBuilder(node.value).build()
        else:
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
        debug_print('visit_BinOp', dump(node))
        l_typ = self.visit(node.left)
        r_typ = self.visit(node.right)
        return union(l_typ, r_typ)

    def visit_Constant(self, node: Constant) -> type:
        return type(node.value)

    def visit_Call(self, node: Call) -> Typ:
        debug_print('visit_Call', dump(node))
        expected_signature = self.visit(node.func)

        if isinstance(expected_signature, FunctionTyp):
            signature = ImmutableList.of_list(expected_signature)
            return_type = signature.last()
            expected_signature = signature.discard_last()

            provided_args = ImmutableList.of_list([self.visit(arg) for arg in node.args])
            self.compare_function_arguments_and_parameters("your method", provided_args, expected_signature)
            return return_type

        return expected_signature

    def visit_ClassDef(self, node: ClassDef) -> None:
        debug_print('visit_ClassDef', dump(node))

        self.dup()

        self.inside_class = True
        self.visit(Module(node.body))
        self.inside_class = False
        env = self.pop()

        self.get_latest_scope().bind_nested(node.name, env)

    def visit_While(self, node: While) -> None:
        debug_print('visit_While', dump(node))
        self.visit(node.test)
        for stm in node.body:
            self.visit(stm)

    def visit_For(self, node: For) -> None:
        debug_print('visit_For', dump(node))
        target = self.visit(node.target)
        ite = self.visit(node.iter)
        self.bind_var(target, ite)
        for stm in node.body:
            self.visit(stm)

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

    def visit_Return(self, node: Return) -> Any:
        debug_print('visit_Return', dump(node))

        return_type = self.visit(node.value)

        return self.compare_type_to_latest_func_return_type(return_type)

    def visit_If(self, node: If) -> None:
        debug_print('visit_If', dump(node))

        self.visit(node.test)
        for stm in node.body:
            self.visit(stm)

        if node.orelse:
            for stm in node.orelse:
                self.visit(stm)

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        debug_print('visit_ImportFrom', dump(node))
        mod_name = f'{node.module}.py'
        if mod_name in sys.builtin_module_names:
            return
        ch_to_mod_dir(mod_name)
        typed_file = typechecker_from_path(mod_name)
        import_env = typed_file.get_latest_scope()
        to_import: Set[str] = {alias.name for alias in node.names}  # addition, zero

        for im in to_import:
            if import_env.contains_function(im):
                self.get_latest_scope().bind_func(im, import_env.lookup_func(im))
            elif import_env.contains_variable(im):
                self.bind_var(im, import_env.lookup_var(im))

    def visit_Import(self, node: Import) -> Any:
        debug_print('visit_Import', dump(node))
        for module in node.names:
            module_name = module.name
            if module_name in sys.builtin_module_names:
                continue
            mod_name = f'{module_name}.py'
            ch_to_mod_dir(mod_name)
            typed_file = typechecker_from_path(mod_name)
            env = typed_file.get_latest_scope()
            self.get_latest_scope().bind_nested(module_name, env)

    def compare_function_arguments_and_parameters(self, func_name, arguments: ImmutableList, parameters: ImmutableList):
        fail_if(not len(arguments) == len(parameters),
                f'function {func_name} expected {len(parameters)} argument{"s" if len(parameters) > 1 else ""} got {len(arguments)}')
        for actual_type, expected_type in zip(arguments.items(), parameters.items()):
            if isinstance(expected_type, str):  # alias
                _, expected_type = self.get_latest_scope().lookup(expected_type)

            types_differ: bool = expected_type != actual_type
            can_upcast: bool = can_upcast_to(actual_type, expected_type)
            fail_if(types_differ and not can_upcast,
                    f'function <{func_name}> expected {parameters}, got {arguments}')

    def compare_type_to_latest_func_return_type(self, return_type: Typ):
        expected_return_type = self.get_current_function_return_type()
        fail_if_cannot_cast(return_type, expected_return_type,
                            f'return type {return_type} did not match {expected_return_type}')
        return return_type

    def is_session_type(self, node):
        return isinstance(node, Subscript) and isinstance(node.value, Name) and node.value.id == 'Channel'

    def get_return_type(self, node: FunctionDef):
        return self.visit(node.returns) if node.returns else Any

    def push(self) -> None:
        self.environments = self.environments.add(Environment())

    def dup(self) -> None:
        prev_env = copy.deepcopy(self.get_latest_scope())
        self.environments = self.environments.add(prev_env)

    def pop(self) -> Environment:
        latest_scope = self.get_latest_scope()
        self.environments = self.environments.discard_last()
        return latest_scope

    def get_latest_scope(self) -> Environment:
        return self.environments.last()

    def get_current_function_return_type(self):
        current_function: FunctionDef = self.in_functions.last()
        ty = self.get_return_type(current_function)
        return ty

    def lookup_or_self(self, k):
        return self.get_latest_scope().lookup_or_default(k, k)

    def bind_var(self, var: str, typ: Typ) -> None:
        self.get_latest_scope().bind_var(var, typ)

    def print_envs(self) -> None:
        i = 0
        for env in self.environments.items():
            print(f'Env #{i}:', env)
            i += 1


def typechecker_from_path(file) -> TypeChecker:
    src = read_src_from_file(file)
    tree = parse(src)
    tc = TypeChecker(tree)
    return tc


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expected 1 argument, got 0')
        sys.exit()
    else:
        typechecker_from_path(sys.argv[1])

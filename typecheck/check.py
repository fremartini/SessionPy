import sys
import ast
import os
import typing  # for accessing _GenericAlias
from ast import *
from typing import *
from types import GenericAlias
from pydoc import locate, safeimport

# For interopability with typing, our type must be all of the following
FunctionTyp = list  # of types
ContainerType = Union[typing._GenericAlias, GenericAlias]
Typ = Union[type, FunctionTyp, ContainerType]
Environment = dict[str, Typ]


def _read_src_from_file(file) -> str:
    with open(file, "r") as f:
        return f.read()


def dump_ast(s, node) -> None:
    print(f'{s}\n', dump(node, indent=4))


# Debug method for checking what a thing is
def is_a(obj):
    print(obj, 'is a', type(obj))


class UnionError(Exception):
    ...


def is_type(maybe_typ):
    return isinstance(type(maybe_typ), Typ)


def union(t1: Typ, t2: Typ) -> Typ:
    if t1 == t2: return t1
    numerics: List[type] = [float, complex, int, bool, Any]  # from high to low
    sequences: List[type] = [str, tuple, bytes, list, bytearray, Any]
    if t1 in numerics and t2 in sequences or t1 in sequences and t2 in numerics:
        raise TypeError(f'cannot merge different hierarchies of {t1} and {t2}')
    for typ_hierarchy in [numerics, sequences]:
        if t1 in typ_hierarchy and t2 in typ_hierarchy:
            for typ in typ_hierarchy:
                if t1 == typ or t2 == typ:
                    return typ
    # Check if from typing module, i.e. List, Sequence, Tuple, etc.
    if isinstance(t1, ContainerType) and isinstance(t2, ContainerType):
        if t1._name != t2._name:
            raise TypeError("cannot union different typing constructs")

        if t1._name == 'Tuple':
            res = []
            for typ1, typ2 in zip(t1.__args__, t2.__args__):
                res.append(union(typ1, typ2))
            return Tuple[res[0], res[1]]
        elif t1._name == 'List':
            t1, t2 = t1.__args__[0], t2.__args__[0]
            return List[union(t1, t2)]
        else:
            raise TypeError(f"cannot union {t1._name} yet")

        # TODO: Extend with other collections 
    else:
        if issubclass(t1, t2):
            return t2
        elif issubclass(t2, t1):
            return t1
        else:
            raise TypeError(f"exhausted: could not union {t1} with {t2}")


def fail_if(e: bool, msg: str) -> None:
    if e:
        raise Exception(msg)


def op_to_str(op):
    match type(op):
        case ast.Add:
            return "__add__"
        case ast.Sub:
            return "__sub__"
        case ast.Mult:
            return "__mul__"


def can_upcast_to(t1: type, t2: type):
    if t2 == Any:
        return True

    # FIXME: issubclass is broken => issubclass(int, float) -> false. Find better solution
    return False


def can_downcast_to(t1: type, t2: type):
    if t1 == Any:
        return True

    # FIXME: issubclass is broken => issubclass(int, float) -> false. Find better solution
    return False


class TypeChecker(NodeVisitor):

    def __init__(self, tree, ignore_imports=False) -> None:
        self.environments: List[Environment] = [{}]
        self.ignore_imports = ignore_imports
        if not ignore_imports:
            self.import_envs: Environment = {}  # {'arith': { 'add': <type signature> }, ... }
        self.visit(tree)

    """
        Check if module given as a string is a Python library; otherwise it's
        local
        
        Example:
        {os, sys, typing, ast, ..}  => true
        [local module]              => false 
    """

    def is_py_lib(self, module_name: str) -> bool:
        if module_name == 'sys':
            return True
        mod = locate(module_name)
        if mod:
            def get_dir(path: str):
                return os.path.dirname(os.path.realpath(path))

            # if path to module is outside of current dir, it's assumed to be library
            return get_dir(__file__) != get_dir(mod.__file__)
        else:
            raise Exception(f"Module <{module_name}> could not be found locally, or in library")

    """
        Handles
            
            from X import Y, Z
        
        We typecheck the file X, bring top-level declarations into scope and
        trim away everything but {Y, Z} and finally merges with out top-decls.
    """

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        if self.ignore_imports:
            return
        mod_name = node.module
        module = safeimport(mod_name)
        if self.is_py_lib(mod_name):
            return
        typed_file: TypeChecker = typecheck_file(module.__file__, ignore_imports=True)
        merging_env = typed_file.get_latest_scope()
        import_names: Set[str] = {alias.name for alias in node.names}
        for k in list(merging_env):
            if k not in import_names:
                del merging_env[k]
        self.environments[0] |= merging_env

    def visit_Import(self, node: Import) -> Any:
        if self.ignore_imports:
            return
        for module in node.names:
            module_name = module.name
            if self.is_py_lib(module_name):
                continue
            module = safeimport(module_name)
            typed_file = typecheck_file(module.__file__, ignore_imports=True)
            env = typed_file.get_latest_scope()
            self.import_envs[module_name] = env

    def visit_Module(self, node: Module) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        ret = self.visit(node.returns) if node.returns else None
        loc_ret = locate(ret) if ret else None
        expected_return_type: type = loc_ret if loc_ret else Any
        parameter_types: List[Tuple[str, type]] = self.visit(node.args)
        parameter_types = [ty for (_, ty) in parameter_types]
        parameter_types.append(expected_return_type)
        self.bind(node.name, parameter_types)

        self.dup()

        args = self.visit(node.args)
        for (v, t) in args:
            self.bind(v, t)

        for stmt in node.body:
            match stmt:
                case _ if isinstance(stmt, Return):
                    actual_return_type = self.visit(stmt)
                    types_differ: bool = actual_return_type != expected_return_type
                    can_downcast: bool = can_downcast_to(expected_return_type, actual_return_type)
                    fail_if(types_differ and not can_downcast,
                            f'expected return type {expected_return_type} got {actual_return_type}')
                case _:
                    self.visit(stmt)

        self.pop()

    def visit_arguments(self, node: arguments) -> List[Tuple[str, type]]:
        arguments: List[type] = []
        for arg in node.args:
            arguments.append(self.visit_arg(arg))
        return arguments

    """
        Visits attributes that forms:
            X.Y(...)
        
        If called on object from other file, returns function name (Y) and the
        type signature of function as a tuple.
    """

    def visit_Attribute(self, node: Attribute) -> Tuple[str, Typ]:
        attr_value = self.visit(node.value)
        if attr_value in self.import_envs:  # calling member of imported file
            return node.attr, self.import_envs[attr_value][node.attr]

    def visit_arg(self, node: arg) -> Tuple[str, type]:
        match node:
            case node if node.annotation:
                ann: str = self.visit(node.annotation)
                ann_typ: type = self.locate_or_lookup(ann)
                assert (type(ann_typ) == type)
                return node.arg, ann_typ
            case _:
                return node.arg, Any

    def visit_Name(self, node: Name) -> str:
        # TODO: consider return (node.id, lookup(node.id)) to easily pass types around
        return node.id

    def visit_Assign(self, node: Assign) -> None:
        # FIXME: handle case where node.targets > 1
        assert (len(node.targets) == 1)

        target: str = self.visit(node.targets[0])

        match node.value:
            case _ if isinstance(node.value, Name):
                # number = int
                # number = x
                value: type = self.locate_or_lookup(self.visit(node.value))
            case _:
                value: type = self.visit(node.value)

        self.bind(target, value)

    def visit_Subscript(self, node: Subscript) -> Any:
        container_str: str = self.visit(node.value)
        container_typ: type = locate(container_str.lower())
        opt_typ = self.visit(node.slice)
        typ: type = locate(opt_typ) if isinstance(opt_typ, str) else opt_typ
        res = container_typ[typ] if container_typ else typ
        return res

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        target: str = self.visit(node.target)
        name_or_type = self.visit(node.annotation)
        if is_type(name_or_type):
            self.bind(target, name_or_type)
        else:
            ann_type: Type = locate(name_or_type)
            assert (type(ann_type) == type)
            rhs_type: Type = self.visit(node.value)
            fail_if(not ann_type == rhs_type, f'annotated type {ann_type} does not match inferred type {rhs_type}')
            self.bind(target, ann_type)

    def visit_BinOp(self, node: BinOp) -> type:
        # op_str = op_to_str(node.op)
        # if not hasattr(node.left, op_str):
        #    raise Exception(f"left operand does not support {op_str}")
        # if not hasattr(node.right, op_str):
        #    raise Exception(f"right operand does not support {op_str}")
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

    def visit_Call(self, node: Call) -> Typ:
        def _class_def():
            self.bind(self.visit(node.func), ClassVar)
            return ClassVar

        def _call():
            name: str = self.visit(node.func)

            args_types: List[Typ] = []
            for arg in node.args:
                match arg:
                    case arg if isinstance(arg, Name):
                        args_types.append(self.lookup(self.visit(arg)))
                    case _:
                        args_types.append(self.visit(arg))

            expected_args: List[Typ] = self.lookup(name)
            return_type: Typ = expected_args.pop()

            fail_if(not len(args_types) == len(expected_args),
                    f'function {name} expected {len(expected_args)} got {len(args_types)}')

            for actual_type, expected_type in zip(args_types, expected_args):
                types_differ: bool = expected_type != actual_type
                can_upcast: bool = can_upcast_to(actual_type, expected_type)

                fail_if(types_differ and not can_upcast,
                        f'function {name} expected {expected_args}, got {args_types}')
            return return_type

        func_name_or_type = self.visit(node.func)
        if type(func_name_or_type) == str:
            name = func_name_or_type
            builtin = locate(name)
            if builtin:
                if is_type(builtin):
                    return builtin
                else:
                    return type(builtin)
            match node:
                case _ if self.lookup(name) == ClassDef:
                    return _class_def()
                case _:
                    return _call()
        elif type(func_name_or_type) == tuple:  # TODO: for now, asserting FunctionType
            fname, typ = func_name_or_type
            args_types: List[Typ] = []
            for arg in node.args:
                match arg:
                    case arg if isinstance(arg, Name):
                        args_types.append(self.lookup(self.visit(arg)))
                    case _:
                        args_types.append(self.visit(arg))
            typ.pop()
            if args_types != typ:
                raise TypeError(f'{fname} expected {typ}, got {args_types}')
            return func_name_or_type

    def visit_Return(self, node: Return) -> Type:
        match node:
            case _ if isinstance(node.value, Name):
                return self.lookup(self.visit(node.value))
            case _:
                return self.visit(node.value)

    def visit_ClassDef(self, node: ClassDef) -> None:
        self.bind(node.name, ClassDef)

    def locate_or_lookup(self, s: str) -> Type:
        loc: Type = locate(s)
        if loc is None:
            return self.lookup(s)
        else:
            return loc

    def push(self) -> None:
        self.environments.append({})

    def dup(self) -> None:
        self.environments.append(self.get_latest_scope())

    def pop(self) -> None:
        self.environments.pop()

    def lookup(self, key) -> type | List[type]:
        latest_scope: Dict[str, Typ] = self.get_latest_scope()
        fail_if(key not in latest_scope, f'{key} was not found in {latest_scope}')
        return latest_scope[key]

    def get_latest_scope(self) -> Dict[str, Typ]:
        return self.environments[len(self.environments) - 1]

    def bind(self, var: str, typ: type) -> None:
        latest_scope: Dict[str, Typ] = self.get_latest_scope()
        latest_scope[var] = typ

    def print_envs(self) -> None:
        print(self.environments)

    def get_envs(self):
        return self.environments


def typecheck_file(file, ignore_imports=False) -> None:
    src = _read_src_from_file(file)
    tree = parse(src)
    return TypeChecker(tree, ignore_imports)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expected 1 argument, got 0')
        sys.exit()
    else:
        typecheck_file(sys.argv[1])

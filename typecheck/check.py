import ast
import typing  # for accessing _GenericAlias
from ast import *
from typing import *
import sys

# For interopability with typing, our type must be all of the following
Typ = Union[type, List[type], typing._GenericAlias]

def _read_src_from_file(file) -> str:
    with open(file, "r") as f:
        return f.read()


def dump_ast(s, node) -> None:
    print(f'{s}\n', dump(node, indent=4))


def str_to_typ(s: str) -> Typ:
    # TODO(Johan): There *must* be a better way, Lord have mercy on us!
    match s:
        case 'int':
            return int
        case 'str':
            return str
        case 'float':
            return float
        case 'bool':
            return bool
        case 'Any':
            return Any
        case _:
            raise Exception(f"unknown type {s}")


class UnionError(Exception):
    ...


"""
TODO: Delete, but keep for now
def union(t1: type, t2: type) -> type:
    if t1 == t2: return t1
    match t1, t2:
        case (typ1, typ2) if typ1 is int and typ2 is int: return int
        case (typ1, typ2) if typ1 is int and typ2 is float: return float
        case (typ1, typ2) if typ1 is float and typ2 is int: return float
        case (typ1, typ2): raise UnionError(f"Cannot union {typ1} with {typ2}")
"""


# TODO: Enforce subtyping, i.e. List[int] <: List[float]
# Currently a problem due to typing's constructs != type
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
    if isinstance(t1, typing._GenericAlias) and isinstance(t2, typing._GenericAlias):
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

    #FIXME: issubclass is broken => issubclass(int, float) -> false. Find better solution
    return False


def can_downcast_to(t1: type, t2: type):
    if t1 == Any:
        return True

    # FIXME: issubclass is broken => issubclass(int, float) -> false. Find better solution
    return False


class TypeChecker(NodeVisitor):


    def __init__(self, tree) -> None:
        self.environments: List[Dict[str, Typ]] = [{}]
        self.visit(tree)

    def visit_Module(self, node: Module) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        expected_return_type: type = Any if not node.returns else str_to_typ(self.visit(node.returns))
        parameter_types: List[Tuple[str, type]] = self.visit(node.args)
        parameter_types = [ty for (_, ty) in parameter_types]
        parameter_types.append(expected_return_type)
        self.bind(node.name, parameter_types)

        self.dup()

        args = self.visit(node.args)
        for pair in args:
            v, t = pair
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

    def visit_arg(self, node: arg) -> Tuple[str, type]:
        match node:
            case node if node.annotation:
                ann: str = self.visit(node.annotation)
                ann_typ: type = str_to_typ(ann)
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
        value: type = self.visit(node.value)
        self.bind(target, value)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        target: str = self.visit(node.target)
        ann_type: Type = str_to_typ(self.visit(node.annotation))
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

    def visit_Call(self, node: Call) -> Any:
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

        match node:
            case _ if self.lookup(self.visit(node.func)) == ClassDef:
                return _class_def()
            case _:
                _call()

    def visit_Return(self, node: Return) -> Type:
        match node:
            case node if isinstance(node.value, Name):
                return self.lookup(self.visit(node.value))
            case _:
                return self.visit(node.value)

    def visit_ClassDef(self, node: ClassDef) -> None:
        self.bind(node.name, ClassDef)

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


def typecheck_file(file) -> None:
    src = _read_src_from_file(file)
    tree = parse(src)
    TypeChecker(tree)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expected 1 argument, got 0')
        sys.exit()
    else:
        typecheck_file(sys.argv[1])

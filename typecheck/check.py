import sys
from ast import *
from pydoc import locate
from check_debug import *
from check_lib import *
from functools import reduce



def last_elem(lst: List[Any]) -> Any:
    return lst[len(lst) - 1]


class TypeChecker(NodeVisitor):

    def __init__(self, tree) -> None:
        self.environments: List[Environment] = [{}]
        self.visit(tree)

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
                    if expected_return_type == Any and actual_return_type and actual_return_type != Any:
                        parameter_types.pop()
                        parameter_types.append(actual_return_type)
                        self.bind(node.name, parameter_types)
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
    
    def visit_List(self, node: List) -> None:
        if DEBUG:
            print('visit_List', dump(node))
        if node.elts:
            list_types: List[Typ] = [self.visit(el) for el in node.elts]
            return List[reduce(union, list_types)]
        else:
            raise Exception("TODO Johan: I assume list contains elts, let's keep this exception for now and investigate if this is thrown...")
    def visit_AnnAssign(self, node: AnnAssign) -> None:
        if DEBUG:
            print('visit_AnnAssign', dump(node))
        target: str = self.visit(node.target)
        ann_type: Type = locate(self.visit(node.annotation))
        assert (type(ann_type) == type)
        rhs_type: Type = self.visit(node.value)
        fail_if(not ann_type == rhs_type, f'annotated type {ann_type} does not match inferred type {rhs_type}')

        self.bind(target, ann_type)

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
            return_type: Typ = last_elem(expected_args)

            fail_if(not len(args_types) == len(expected_args) - 1,
                    f'function {name} expected {len(expected_args)} got {len(args_types)}')

            for actual_type, expected_type in zip(args_types, expected_args):
                types_differ: bool = expected_type != actual_type
                can_upcast: bool = can_upcast_to(actual_type, expected_type)

                fail_if(types_differ and not can_upcast,
                        f'function {name} expected {expected_args}, got {args_types}')
            return return_type
        func_name = self.visit(node.func)
        builtin = locate(func_name)
        if builtin:
            if type(builtin) == type:
                return builtin
            else:
                return type(builtin)
        match node:
            case _ if self.lookup(func_name) == ClassDef:
                return _class_def()
            case _:
                _call()
    
    def visit_Subscript(self, node: Subscript) -> Any:
        container_str: str = self.visit(node.value)
        container_typ: type = locate(container_str.lower())
        container_typ = to_typing(container_typ)
        opt_typ = self.visit(node.slice)
        typ: type = locate(opt_typ) if isinstance(opt_typ, str) else opt_typ
        res = container_typ[typ] if container_typ else typ
        return res

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

    def get_latest_scope(self) -> Environment:
        return last_elem(self.environments)

    def bind(self, var: str, typ: type) -> None:
        if DEBUG:
            print(f'bind: binding {var} to {typ}')
        latest_scope: Dict[str, Typ] = self.get_latest_scope()
        latest_scope[var] = typ

    def print_envs(self) -> None:
        print(self.environments)


def typecheck_file(file) -> None:
    src = read_src_from_file(file)
    tree = parse(src)
    TypeChecker(tree)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expected 1 argument, got 0')
        sys.exit()
    else:
        typecheck_file(sys.argv[1])

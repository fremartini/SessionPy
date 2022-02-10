import inspect
from ast import *
from typing import *
from textwrap import dedent
from typesystem import *

def check(f : callable) -> callable:
    file = dedent(inspect.getfile(f))         
    src = _read_src_from_file(file)
    tree = parse(src)
    TypeChecker(tree)
    return f

def _read_src_from_file(file) -> Str:
    with open(file, "r") as f:
        return f.read()

def dump_ast(s, node) -> None:
    print(f'{s}\n', dump(node, indent=4))

def str_to_typ(s : str) -> Typ:
    # TODO(Johan): There *must* be a better way, Lord have mercy on us!
    match s:
        case 'int': return int
        case 'str': return str
        case 'float': return float
        case 'bool': return bool
        case _: raise Exception(f"unknown type {s}")

class UnionError(Exception):
    ...

def union(t1: type, t2: type) -> type:
    if t1 == t2: return t1
    match t1, t2:
        case (typ1, typ2) if typ1 is int and typ2 is int: return int
        case (typ1, typ2) if typ1 is int and typ2 is float: return float
        case (typ1, typ2) if typ1 is float and typ2 is int: return float
        case (typ1, typ2): raise UnionError(f"Cannot union {typ1} with {typ2}")

class TypeChecker(NodeVisitor):
    def __init__(self, tree) -> None:
        # Union[int, str] = int | str
        # [x -> int
        # add -> [int, int, int]]
        self.environments : List[Dict[str, type | List[type]]] = [{}] 
        self.visit(tree)

    def visit_Module(self, node: Module) -> None:
        for stmt in node.body:
            self.visit(stmt)
        self.print_envs()

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        return_type : type = Any if not node.returns else str_to_typ(self.visit(node.returns))
        parameter_types : List[Tuple[str, type]] = self.visit(node.args)
        parameter_types = [ty for (_,ty) in parameter_types]
        parameter_types.append(return_type)
        self.bind(node.name, parameter_types)

        self.push()
        
        args = self.visit(node.args)
        for pair in args:
            v, t = pair
            self.bind(v, t)

        for stmt in node.body:
            self.visit(stmt)

        self.print_envs()
        self.pop()

    def visit_arguments(self, node: arguments) -> List[Tuple[str, type]]:
        arguments = []

        for arg in node.args:
            arguments.append(self.visit_arg(arg))

        return arguments

    def visit_arg(self, node: arg) -> Tuple[str, type]:
        match node:
            case node if node.annotation:
                ann : str = self.visit(node.annotation)
                ann_typ : type = str_to_typ(ann)
                return (node.arg, ann_typ)
            case _:
                return (node.arg, Any)

    def visit_Name(self, node: Name) -> Str:
        # TODO: consider return (node.id, lookup(node.id)) to easily pass types around
        return node.id

    def visit_Assign(self, node: Assign) -> None:
        #FIXME: handle case where node.targets > 1
        assert(len(node.targets) == 1)

        target : str = self.visit(node.targets[0])
        value : type = self.visit(node.value)
        self.bind(target, value)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        target : str = self.visit(node.target)
        ann : Type = str_to_typ(self.visit(node.annotation))
        #FIXME: consider annotated vs inferred type?
        #value : Type = self.visit(node.value)
        #assert ann == value

        self.bind(target, ann)

    def visit_BinOp(self, node: BinOp) -> type:
        l = self.visit(node.left)
        r = self.visit(node.right)
        if isinstance(l, str):
            l = self.lookup(l) 
        if isinstance(r, str):
            r = self.lookup(r)
        return union(l, r)

    def visit_Constant(self, node: Constant) -> Type:
        return type(node.value)

    def visit_Call(self, node: Call) -> Any:
        return Any

    def visit_Return(self, node: Return) -> Type:
        return self.lookup(self.visit(node.value))

    def push(self) -> None:
        self.environments.append({})

    def dup(self) -> None:
        self.environments.append(self.get_latest_scope())

    def pop(self) -> None:
        self.environments.pop()

    def lookup(self, key) -> Type:
        latest_scope : Dict[str, type] = self.get_latest_scope()

        if (key in latest_scope):
            return latest_scope[key]  
        else:
            raise Exception(f'{key} was not found in {latest_scope}')  
        
    def get_latest_scope(self) -> Dict[str, type]:
        return self.environments[len(self.environments)-1]

    def bind(self, var, val) -> None:
        latest_scope : Dict[str, type] = self.get_latest_scope()
        latest_scope[var] = val

    def print_envs(self) -> None:
        print(self.environments)
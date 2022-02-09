import inspect
from ast import *
from typing import *
from textwrap import dedent
import types

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

def str_to_typ(s : str) -> type:
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
        self.environments : List[Dict[str, type]] = [{}] 
        self.visit(tree)

    def visit_Module(self, node: Module) -> None:
        for stmt in node.body:
            print(self.environments)
            self.visit(stmt)

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        self.push()
        self.visit(node.args)
        for stmt in node.body:
            self.visit(stmt)
        print(self.environments)
        self.pop()

    def visit_arguments(self, node: arguments) -> None:
        for arg in node.args:
            self.visit_arg(arg)

    def visit_arg(self, node: arg) -> None:
        match node:
            case node if node.annotation:
                ann : str = self.visit(node.annotation)
                ann_typ : type = str_to_typ(ann)
                self.bind(node.arg, ann_typ)
            case _:
                self.bind(node.arg, Any)

    def visit_Name(self, node: Name) -> Str:
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
        l_typ = self.lookup(l)
        r_typ = self.lookup(r)
        return union(l_typ, r_typ)

    def visit_Constant(self, node: Constant) -> Type:
        return type(node.value)

    def visit_Call(self, node: Call) -> Any:
        return Any

    def push(self) -> None:
        self.environments.append({})

    def pop(self) -> None:
        self.environments.pop()

    def lookup(self, key) -> Type:
        latest_scope : Dict[str, type] = self.get_latest_scope()

        print(f'trying to find {key} in {latest_scope}')
        if (key in latest_scope):
            return latest_scope[key]  
        else:
            raise Exception(f'{key} was not found in {latest_scope}')  
        
    def get_latest_scope(self) -> Dict[str, type]:
        return self.environments[len(self.environments)-1]

    def bind(self, var, val) -> None:
        latest_scope : Dict[str, type] = self.get_latest_scope()
        latest_scope[var] = val
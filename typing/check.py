import inspect
from ast import *
from typing import *
from textwrap import dedent

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

def strToTyp(s):
    match s:
        case 'int': return int
        case 'str': return str
        case 'bool': return bool
        case _: raise Exception(f"unknown type {s}")

class TypeChecker(NodeVisitor):
    def __init__(self, tree) -> None:
        self.environments : List[Dict[str, type]] = [{}] 
        self.visit(tree)

    def visit_Module(self, node: Module) -> None:
        for stmt in node.body:
            dump_ast("#STMT", stmt)
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
                ann_typ : type = strToTyp(ann)
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
        ann : Type = strToTyp(self.visit(node.annotation))
        #FIXME: consider annotated vs inferred type?
        #value : Type = self.visit(node.value)
        #assert ann == value

        self.bind(target, ann)

    def visit_Constant(self, node: Constant) -> Type:
        return type(node.value)

    def visit_Call(self, node: Call) -> Any:
        return Any

    def push(self) -> None:
        self.environments.append({})

    def pop(self) -> None:
        self.environments.pop()

    def bind(self, var, val) -> None:
        latest_scope : Dict[str, type] = self.environments[len(self.environments)-1]
        latest_scope[var] = val
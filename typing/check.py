import inspect
from ast import *
from typing import *
from textwrap import dedent

def check(f):
    file = dedent(inspect.getfile(f))         
    src = _read_src_from_file(file)
    tree = parse(src)
    GradualTypeChecker(tree)

def _read_src_from_file(file):
    with open(file, "r") as f:
        return f.read()

def dump_ast(s, node):
    print(f'{s}\n', dump(node, indent=4))

class GradualTypeChecker(NodeVisitor):
    def __init__(self, tree) -> None:
        self.env = {}
        self.visit(tree)

    def visit_Assign(self, node: Assign) -> Any:
        dump_ast("ASSIGN#", node)

    def visit_AnnAssign(self, node: AnnAssign) -> Any:
        dump_ast("ANN-ASSIGN#", node)

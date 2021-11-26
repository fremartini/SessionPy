from ast import *

class Scanner(NodeVisitor):
    def __init__(self, file_ast):
        self.file_ast = file_ast
        self.functions = {}

    def run(self):
        self.visit(self.file_ast)
        return (self.functions)

    def visit_FunctionDef(self, node: FunctionDef):
        args = node.args
        assert(isinstance(args, arguments))
        args = args.args
        for a in args:
            assert(isinstance(a, arg))
            ann = a.annotation.id               #type annotation : 'Channel'
            a = a.arg                           #variable name : 'c'
            if (str.lower(ann) == 'channel'):
                self.functions[node.name] = node
                return
            
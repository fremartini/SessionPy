import ast
from pprint import pprint
from util import dump
from sys import argv, exit


def main(args):
    with open(args[0], "r") as source:
        tree = ast.parse(source.read())

    analyzer = Analyzer()
    analyzer.visit(tree)
    analyzer.report()


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.stats = {"import": [], "from": [], "def": [], "entrypoint": None}

    def visit_Import(self, node):
        for alias in node.names:
            self.stats["import"].append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.stats["from"].append(alias.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        for dec in node.decorator_list:
            if dec.id == 'check_file': # at this point, we should start traversal of tree
                if self.stats["entrypoint"] == None:
                    self.stats["entrypoint"] = node
                else:
                    exit("err! only one funcdef can have @check_file decoration")
                self.verify_channels(node.body)

        self.stats["def"].append(node.name)
        self.generic_visit(node)

    def verify_channels(self, nd):
        for stmt in nd:
            if stmt.__class__ == ast.Assign:
                self.check_assign(stmt)

    def check_assign(self, asgn):
        dump('assignment', asgn)
        t, v = *asgn.targets, asgn.value # TODO: only allowing 1:1 assignment mapping (not i.e. ch1, ch2 = Channel(), Channel())
        dump("target", t)
        dump("value", v())
        dump('call.func', v.func)

    def report(self):
        pprint(self.stats)


if __name__ == "__main__":
    main(argv[1:])
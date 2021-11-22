import ast
from pprint import pprint
from util import dump
from sys import argv, exit
import textwrap
import inspect

def verify_channels(f):
    src = textwrap.dedent(inspect.getsource(f))
    tree = ast.parse(src)
    analyzer = Analyzer()
    analyzer.visit(tree)

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
            if dec.id == 'verify_channels': # at this point, we should start traversal of tree
                if self.stats["entrypoint"] == None:
                    self.stats["entrypoint"] = node
                else:
                    exit("err! only one funcdef can have @check_file decoration")
                self.verify_channels(node.body)

        self.stats["def"].append(node.name)
        self.generic_visit(node)

    def verify_channels(self, nd):
        for stmt in nd:
            match stmt:
                case ast.Assign(): self.check_assign(stmt)
                

    def check_assign(self, asgn):
        t, v = *asgn.targets, asgn.value # TODO: only allowing 1:1 assignment mapping (not i.e. ch1, ch2 = Channel(), Channel())
        # print('assign', t.id, 'to')
        # print(v.id)
        match v:
            case ast.Call(): self.search_call(v)
    
    def search_call(self, call_obj):
        f = call_obj.func
        if isinstance(f, ast.Subscript):
            st = self.search_slice(f.slice)
            print(st) # TODO: this prints our session type

    def search_slice(self, slice_obj):
        if isinstance(slice_obj, ast.Tuple):
            tmp = ''
            for dim in slice_obj.dims:
                if isinstance(dim, ast.Name):
                    tmp += dim.id
                else:
                    assert(isinstance(dim, ast.Subscript))
                    return tmp + ' ' + self.search_slice(dim)
            return tmp
            #for elt in slice_obj.elts: # TODO: this contains the same – investigate which one to keep
            #    print('elt', elt.id)
        if isinstance(slice_obj, ast.Subscript):
            name = slice_obj.value
            assert(isinstance(name, ast.Name))
            return name.id + ' ' + self.search_slice(slice_obj.slice)
        dump('???', slice_obj)
    def report(self):
        pprint(self.stats)


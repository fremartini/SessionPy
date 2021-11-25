import ast
from pprint import pprint
from sessiontype import A
from util import dump
import textwrap
import inspect

def verify_channels(f):
    src = textwrap.dedent(inspect.getsource(f))
    tree = ast.parse(src)
    analyzer = Analyzer()
    analyzer.visit(tree)
    analyzer.report()

class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.channels = {}

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
                self.verify_channels(node.body)

    def verify_channels(self, nd):
        for stmt in nd:
            match stmt:
                case ast.Assign(): self.check_assign(stmt)
                case ast.Call(): self.check_call(stmt)

    def check_call(self, stm):
        dump('check_call', stm)
                
    def check_assign(self, asgn):
        # x = y
        # 1: ch = Channel...
        # 2: <var> = ch.send/recv
        t, v = *asgn.targets, asgn.value # TODO: only allowing 1:1 assignment mapping (not i.e. ch1, ch2 = Channel(), Channel())
        dump('value', v)
        if(isinstance(v, ast.Call)):
            self.check_channel_usage(t, v)
        # print('assign', t.id, 'to')
        # print(v.id)
        match v:
            case ast.Call(): self.search_call(t, v)

    def check_channel_usage(self, target, value):
        dump('check_channel_usage target', target)
        assert(isinstance(target, ast.Name))
        assert(isinstance(value, ast.Call))
        # if target.id in self.channels: # 
        dump("call", value)
        attri = value.func
        if(isinstance(attri, ast.Attribute)): 
            dump('arg', value.args[0])
            channel_name = attri.value.id # channel variable (i.e. c, ch, etc)
            op = attri.attr
            if op == 'send':
                assert(len(value.args) == 1)
                value = value.args[0]
                if isinstance(value, ast.Constant):
                    value = value.value
                st = self.channels[channel_name]
                valTyp = str(type(value))
                (action,typ), *tail = st
                self.channels[channel_name] = tail
                # assert(valTyp == typ) #'int' != int
                
    def mapStrToTyp(s):
        match s:
            case 'int': return int
            case 'str': return str
            case 'bool': return bool
            case _: raise Exception (f"unknown type {s}")

    def search_call(self, target, call_obj):
        f = call_obj.func
        if isinstance(f, ast.Subscript) and f.value.id == 'Channel': 
            
            # Essentially, typing information is within a Subscript
            """
            A subscript, such as l[1]. value is the subscripted object (usually
                    sequence or mapping). slice is an index, slice or key. It
            can be a Tuple and contain a Slice. ctx is Load, Store or Del
            according to the action performed with the subscript.
            """
            st = self.search_slice(f.slice)
            it = iter(st)
            self.channels[target.id] = list(zip(it,it))

    def search_slice(self, sliced):
        acc = []
        if isinstance(sliced, ast.Tuple): 
            dump('tuple', sliced)
            print('tup', [x.id for x in sliced.dims])
            # A tuple of the form (<type>, Subscript) where Subcscript should be recursively called
            for dim in sliced.dims:
                if isinstance(dim, ast.Name):
                    if dim.id != 'End':
                        acc.append(dim.id)
                else:
                    assert(isinstance(dim, ast.Subscript))
                    tmp = self.search_slice(dim)
                    acc += tmp
            #for elt in slice.elts: # TODO: this contains the same – investigate which one to keep
            #    print('elt', elt.id)
        if isinstance(sliced, ast.Subscript):
            name = sliced.value # This is the ast.Name of the action, i.e. Send/Recv/End
            assert(isinstance(name, ast.Name))
            tmp = self.search_slice(sliced.slice)
            acc.append(name.id)
            acc += tmp
        return acc


    def report(self):
        pprint(self.channels)
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
                
    def check_assign(self, asgn):
        # x = y
        # 1: ch = Channel...
        # 2: <var> = ch.send/recv
        t, v = *asgn.targets, asgn.value # TODO: only allowing 1:1 assignment mapping (not i.e. ch1, ch2 = Channel(), Channel())
        if(isinstance(v, ast.Call)):
            self.check_channel_usage(t, v)
        match v:
            case ast.Call(): self.search_call(t, v)

    def check_channel_usage(self, target, value):
        assert(isinstance(target, ast.Name))
        assert(isinstance(value, ast.Call))
        attri = value.func
        if(isinstance(attri, ast.Attribute)):       # channel usage : v = ch.recv()
            channel_name = attri.value.id           
            op = attri.attr
            match op:
                case 'send':                        # only works if send returns something e.g : v = ch.send(10)
                    assert(len(value.args) == 1)
                    value = value.args[0]
                    if isinstance(value, ast.Constant):
                        value = value.value
                    st = self.channels[channel_name]
                    valTyp = type(value)
                    (action,typ), *tail = st
                    assert(valTyp == typ)
                    assert(action == op)
                    self.channels[channel_name] = tail
                case 'recv':
                    assert(len(value.args) == 0)
                    st = self.channels[channel_name]
                    (action,typ), *tail = st        # TODO: ch = Channel[Recv[int, End]]() crashes, not enough values to unpack
                    assert(action == op)
                    self.channels[channel_name] = tail
                    print(self.channels[channel_name])
        elif(isinstance(attri, ast.Subscript)):     # channel definition : ch = Channel[Send[int, End]]()
            ...
                
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
            # A tuple of the form (<type>, Subscript) where Subcscript should be recursively called
            for dim in sliced.dims:
                if isinstance(dim, ast.Name):
                    if dim.id != 'End':
                        acc.append(self.strToTyp(dim.id))
                else:
                    assert(isinstance(dim, ast.Subscript))
                    tmp = self.search_slice(dim)
                    acc += tmp
        if isinstance(sliced, ast.Subscript):
            name = sliced.value # This is the ast.Name of the action, i.e. Send/Recv/End
            assert(isinstance(name, ast.Name))
            tmp = self.search_slice(sliced.slice)
            acc.append(str.lower(name.id))
            acc += tmp
        return acc

    def strToTyp(self, s):
        match s:
            case 'int': return int
            case 'str': return str
            case 'bool': return bool
            case _: raise Exception (f"unknown type {s}")

    def report(self):
        pprint(self.channels)
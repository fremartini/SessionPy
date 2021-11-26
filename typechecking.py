import inspect
import ast
from pprint import pprint
from infer import infer
from scanner import Scanner
from util import *
from textwrap import dedent

def verify_channels(f):
    analyzer = Analyzer(f)
    analyzer.scan()
    analyzer.check()
    return f

class Analyzer(ast.NodeVisitor):
    def __init__(self, func):
        self.func = func
        self.entry = None
        self.channels = {}
        self.functions = {}

    """
    Scan the file the decorated function belongs to, for functions
    that has Channels as parameters
    """
    def scan(self):
        file = dedent(inspect.getfile(self.func))
        src = _read_src_from_file(file)
        tree : ast.Module = ast.parse(src)
        self.functions = Scanner(tree).run()

    """
    Check that Channels are used correctly in all functions which they are used
    """
    def check(self):
        src = dedent(inspect.getsource(self.func))
        tree = ast.parse(src)
        self.visit(tree)
        self.check_channel_postcondition()

    def visit_FunctionDef(self, node):
        for dec in node.decorator_list:
            if dec.id == 'verify_channels': 
                if self.entry != None:
                    raise Exception('multiple defs with @verify_channels found')
                self.entry = node
                self.verify_channels(node.body)

    def verify_channels(self, nd):
        for stmt in nd:
            dump_ast(stmt)
            match stmt:
                case ast.Assign(): self.check_assign(stmt)
                case ast.Expr(): self.check_expr(stmt)

    def check_channel_postcondition(self):
        """ 
        If a session-type list is not empty, it has not been used in
        accordance with its type: throw error.  
        """
        errors = []
        for ch_name, ch_ops in self.channels.items():
            if ch_ops:
                errors.append(f'channel "{ch_name}" is not exhausted {ch_ops}')

        if errors:
            raise Exception (f"ill-typed program: {errors}")

    def check_expr(self, expr):
        assert(isinstance(expr, ast.Expr))
        if isinstance(expr.value, ast.Call):
            self.check_call(expr.value)

    """
    In this function, we check for following two scenarios: 
     * ch = Channel...
     * <var> = ch.send/recv
    First, if we assign a channel to a variable, our dictionary should be updated with session type.
    Second, if some variable is assigned to a call to our channel, we should progress ST/validate types.
    """
    def check_assign(self, asgn):
        assert(isinstance(asgn, ast.Assign))
        t, v = *asgn.targets, asgn.value 
        if isinstance(v, ast.Call):
            self.check_call(v)
            self.if_channel_add_to_dict(t, v)

    """
        Extracts type and method for a a call object right now ASSUMED to be a
        channel.  
        
        Examples: 
         * ch.send(42) or ch.send(f())
         * c.recv() 

        In the first case, we need to validate that type of argument (42, f())
        matches the current action and type of our session type.  
    """
    def check_call(self, call):
        assert(isinstance(call, ast.Call))
        call_func = call.func
        call_args = call.args
        if(isinstance(call_func, ast.Attribute)):       # this structure: x.y()
                                                        #                 ^ attribute
            channel_name = call_func.value.id           
            op = call_func.attr
            match op:
                case 'send':
                    assert(len(call_args) == 1)
                    arg_typ = infer(call_args[0])
                    st = self.channels[channel_name]
                    if not st:
                        raise Exception("Channel has been exhausted of operations")

                    (action,typ), *tail = st
                    assertEq(typ, arg_typ)
                    assertEq(action, op)
                    self.channels[channel_name] = tail
                case 'recv':
                    assert(len(call_args) == 0)
                    st = self.channels[channel_name]
                    if not st:
                        raise Exception("Channel has been exhausted of operations")
                    (action,typ), *tail = st        # TODO: ch = Channel[Recv[int, End]]() crashes, not enough values to unpack
                    assertEq(action, op)
                    self.channels[channel_name] = tail
        elif isinstance(call_func, ast.Name): # structure: print(), f(), etc.
                                              #            ^^^^^    ^ - Name
            func_name = call.func.id
            for arg in call_args:
                # we have a function call with a channel
                if isinstance(arg, ast.Name) and arg.id in self.channels: 
                    #get func from file
                    self.verify_channels(self.functions[func_name].body)
                
    """
    If the channel contains a subscript e.g ch = Channel[Recv[int, End]]()
    extract the typing information contained within the subscript and add it to the global dictionary
    """
    def if_channel_add_to_dict(self, var_name, call_obj):
        assert(isinstance(var_name, ast.Name))
        f = call_obj.func
        if isinstance(f, ast.Subscript) and f.value.id in ['TCPChannel', 'QChannel']:
            
            # Essentially, typing information is within a Subscript
            """
            A subscript, such as l[1]. value is the subscripted object (usually
                    sequence or mapping). slice is an index, slice or key. It
            can be a Tuple and contain a Slice. ctx is Load, Store or Del
            according to the action performed with the subscript.
            """
            st = self.search_slice(f.slice)
            it = iter(st)
            self.channels[var_name.id] = list(zip(it,it)) # store list of tuples [(send, int), (recv, bool) etc.]

    def search_slice(self, sliced):
        acc = []
        if isinstance(sliced, ast.Tuple): 
            # A tuple of the form (<type>, Subscript) where Subcscript should be recursively called
            for dim in sliced.dims:
                if isinstance(dim, ast.Name):
                    if dim.id != 'End':
                        acc.append(strToTyp(dim.id))
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

    def report(self):
        pprint(self.channels)

def strToTyp(s):
    match s:
        case 'int': return int
        case 'str': return str
        case 'bool': return bool
        case _: raise Exception (f"unknown type {s}")

def assertEq(expected, actual):
    if (not expected == actual):
        raise Exception("expected " + str(expected) + ", found " + str(actual))

def _read_src_from_file(file):
    with open(file, "r") as f:
        return f.read()
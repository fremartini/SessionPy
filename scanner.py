import ast
from sessiontype import *

class TypeNode:
    def __init__(self, action, typ) -> None:
        self.action = action
        self.typ = typ
        self.left = None
        self.right = None
    
    def branch(l, r):
        cmd1, typ1 = l
        cmd2, typ2 = r
        node1 = TypeNode(cmd1, typ1)
        node2 = TypeNode(cmd2, typ2)
        return (node1, node2)

    def empty_if_none(self, obj):
        return '' if obj == None else str(obj) + " "

    def __str__(self) -> str:
        return f"[action: {self.action} " + (f'{self.typ} ' if self.typ else '') + (f'left: {self.left} ' if self.left else '') + (f'right: {self.right}' if self.right else '') + "]"

class Scanner(ast.NodeVisitor):
    def __init__(self, file_ast):
        self.file_ast = file_ast
        self.functions = {}
        self.channels = {}
        self.entry = None

    """
    Scans a file AST for channels in the annotated function
    and functions that accepts channels as parameters
    """
    def run(self):
        self.visit(self.file_ast)
        return (self.functions, self.channels)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        for dec in node.decorator_list:
            if dec.id == 'verify_channels': 
                if self.entry != None:
                    raise Exception('multiple defs with @verify_channels found')
                self.entry = node
                self.verify_channels(node.body)

        args = node.args
        assert(isinstance(args, ast.arguments))
        args = args.args
        for a in args:
            assert(isinstance(a, ast.arg))
            ann = a.annotation.id               #type annotation : 'Channel'
            a = a.arg                           #variable name : 'c'
            if (str.lower(ann) == 'channel'):
                self.functions[node.name] = node
                break

    def verify_channels(self, body):
        for stmt in body:
            match stmt:
                case ast.Assign(): self.check_assign(stmt)

    def check_assign(self, asgn):
        assert(isinstance(asgn, ast.Assign))
        t, v = *asgn.targets, asgn.value 
        if isinstance(v, ast.Call):
            self.if_channel_add_to_dict(t, v)

    """
    If the channel contains a subscript e.g ch = Channel[Recv[int, End]]()
    extract the typing information contained within the subscript and add it to the global dictionary
    """
    def if_channel_add_to_dict(self, var_name, call_obj):
        assert(isinstance(var_name, ast.Name))
        f = call_obj.func
        if isinstance(f, ast.Subscript) and f.value.id in ['Channel']:
            
            # Essentially, typing information is within a Subscript
            """
            A subscript, such as l[1]. value is the subscripted object (usually
                    sequence or mapping). slice is an index, slice or key. It
            can be a Tuple and contain a Slice. ctx is Load, Store or Del
            according to the action performed with the subscript.
            """
            st = self.search_slice(f.slice)
            self.channels[var_name.id] = st

    def search_slice(self, func_slice):
        if isinstance(func_slice, ast.Name): # base case: End
            assert (str.lower(func_slice.id) == 'end')
            return None

        tn = None
        action = func_slice.value # This is the ast.Name of the action, i.e. Send/Recv/End
        assert(isinstance(action, ast.Name))
        action = str.lower(action.id)
        if action in ['offer', 'choose']:
            assert(isinstance(func_slice.slice, ast.Tuple))
            st1 = self.search_slice(func_slice.slice.elts[0])
            st2 = self.search_slice(func_slice.slice.elts[1])
            tn = TypeNode(action, None)
            tn.left = st1
            tn.right = st2
        else:
            typ = self.get_concrete_type(func_slice.slice)
            st  = self.get_session_type(func_slice.slice)
            tn = TypeNode(action, strToTyp(typ))
            tn.right = st
        return tn

    def get_concrete_type(self, slice):
        return slice.elts[0].id
    
    def get_session_type(self, slice):
        return self.search_slice(slice.elts[1])

def strToTyp(s):
    match s:
        case 'int': return int
        case 'str': return str
        case 'bool': return bool
        case _: raise Exception (f"unknown type {s}")
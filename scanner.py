import ast

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

def strToTyp(s):
    match s:
        case 'int': return int
        case 'str': return str
        case 'bool': return bool
        case _: raise Exception (f"unknown type {s}")
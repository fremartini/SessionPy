import ast

from util import dump_ast
from infer import infer

class Checker(ast.NodeVisitor):
    def __init__(self, tree, functions, channels):
        self.tree = tree
        self.functions = functions
        self.channels = channels

    def run(self):
        self.visit(self.tree)
        self.verify_postconditions()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        for dec in node.decorator_list:
            if dec.id == 'verify_channels': 
                self.verify_channels(node.body)

    def verify_channels(self, body):
        for stmt in body:
            match stmt:
                case ast.Expr(): self.check_expr(stmt)
                case ast.Assign(): self.check_assign(stmt)


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
                    (action,typ), *tail = st
                    assertEq(action, op)
                    self.channels[channel_name] = tail
        elif isinstance(call_func, ast.Name): # structure: print(), f(), etc.
                                              #            ^^^^^    ^ - Name
            func_name = call.func.id

            for idx, arg in enumerate(call_args):
                if isinstance(arg, ast.Name) and arg.id in self.channels: 
                    func = self.functions[func_name]
                    func_chan_arg = func.args.args[idx].arg

                    self.channels[func_chan_arg] = self.channels[arg.id]
                    self.verify_channels(func.body)
                    self.channels[arg.id] = self.channels[func_chan_arg]
                    self.channels.pop(func_chan_arg)

    def verify_postconditions(self):
        """ 
        If a session-type list is not empty, it has not been used in
        accordance with its type: throw error.  
        """
        errors = []
        for ch_name, ch_ops in self.channels.items():
            if ch_ops:
                errors.append(f'channel "{ch_name}" is not exhausted')

        if errors:
            raise Exception (f"ill-typed program: {errors}")

def assertEq(expected, actual):
    if (not expected == actual):
        raise Exception("expected " + str(expected) + ", found " + str(actual))
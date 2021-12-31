import ast
from enum import Enum

from util import assertEq, dump_ast, strToTyp

class Scope(Enum):
    LEFT = 0
    RIGHT = 1

class Checker(ast.NodeVisitor):
    def __init__(self, func_ast, functions, channels):
        self.func_ast = func_ast
        self.functions = functions
        self.channels = channels
        self.scopes = []
        self.env = {}

    def run(self):
        self.visit(self.func_ast)
        self.verify_postconditions()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        for dec in node.decorator_list:
            if dec.id == 'verify_channels':
                self.verify_channels(node.body)

    def verify_channels(self, stmts):
        for stmt in stmts:
            match stmt:
                case ast.Expr(): self.check_expr(stmt)
                case ast.AnnAssign(): self.check_ann_assign(stmt)
                case ast.Assign(): self.check_assign(stmt)
                case ast.Match(): self.check_match(stmt)
                case ast.If(): self.check_if(stmt)

    def check_expr(self, expr):
        assert(isinstance(expr, ast.Expr))
        if isinstance(expr.value, ast.Call):
            self.check_call(expr.value)

    def check_ann_assign(self, ann):
        assert(isinstance(ann, ast.AnnAssign))
        if isinstance(ann.annotation, ast.Name):
            self.env[ann.target.id] =  strToTyp(ann.annotation.id)
        elif isinstance(ann.annotation, ast.Subscript):
            self.env[ann.target.id] = strToTyp(ann.annotation.value.id)
        elif isinstance(ann.value, ast.Call):
            self.check_call(ann.value)

    def check_assign(self, asgn):
        """
        Look for send, recv, choose, call operations in assign expression
        """
        assert(isinstance(asgn, ast.Assign))
        target, v = *asgn.targets, asgn.value
            
        if isinstance(v, ast.Call):
            self.check_call(v, target)

    def check_match(self, match):
        """
        The offer operation must be used within a match block,
        verify the left and right block
        """
        assert(isinstance(match, ast.Match))

        if self.is_channel_offer(match.subject):
            ch_name = match.subject.func.value.id
            st = self.get_session_type(ch_name)
            self.fail_if_exhausted(st, ch_name)

            cases = match.cases
            assert len(cases) == 2
            for case in cases:
                pattern = case.pattern
                body = case.body
                att = pattern.value.attr
                if att == 'LEFT':
                    self.verify_in_scope(Scope.LEFT, body)
                elif att == 'RIGHT':
                    self.verify_in_scope(Scope.RIGHT, body)
                else:
                    raise Exception("Scope was not left or right")

    def verify_in_scope(self, scope, body):
        self.add_scope(scope)
        self.verify_channels(body)
        self.pop_scope()        

    def check_if(self, expr):
        prev_scope_count = len(self.scopes)
        self.verify_channels(expr.body)
        while prev_scope_count != len(self.scopes):
            self.pop_scope()

        prev_prev_scope_count = len(self.scopes)
        self.verify_channels(expr.orelse)
        while prev_prev_scope_count != len(self.scopes):
            self.pop_scope()

    def check_call(self, call, target = None):
        """
        Check calls that are choose, send, recv or function calls
        """
        assert(isinstance(call, ast.Call))
        call_func = call.func
        call_args = call.args
        if(isinstance(call_func, ast.Attribute)):
            op = call_func.attr
            if op in ['choose', 'send', 'recv']:
                ch_name = call_func.value.id
                st = self.get_session_type(ch_name)
                self.fail_if_exhausted(st, ch_name)
                match op:
                    case 'choose':
                        self.choose(call_args)
                    case 'send':
                        self.send(call_args, op, st, ch_name)
                    case 'recv':
                        self.recv(call_args, op, st, ch_name, target)
            else:
                raise NotImplementedError(f'Operator channel.{op} is not implemented')
        elif isinstance(call_func, ast.Name):
            self.function_call(call, call_args)

    def choose(self, call_args):
        assert(len(call_args) == 1)
        arg = call_args[0]

        assert(arg.value.id == 'Branch')
        left_or_right = arg.attr
        assert left_or_right in ['LEFT', 'RIGHT']
        self.add_scope(Scope.LEFT if left_or_right == 'LEFT' else Scope.RIGHT)

    def recv(self, call_args, op, st, ch_name, target):
        assert(len(call_args) == 0)
        assertEq(st.action, op)

        if not target == None:
            self.env[target.id] =  st.typ
        self.advance(ch_name)

    def send(self, call_args, op, st, ch_name):
        assert(len(call_args) == 1)
        arg_typ = self.infer(call_args[0])
        assertEq(st.typ, arg_typ)
        assertEq(st.action, op)
        self.advance(ch_name)

    def check_attribute(self, att, predX, y):
        """checks <predX(x) and attr.y == y>"""
        assert(isinstance(att, ast.Attribute))
        assert(isinstance(att.value, ast.Name))
        return predX(att.value.id) and att.attr == y

    def is_channel_offer(self, subject):
        return (isinstance(subject, ast.Call) and
                isinstance(subject.func, ast.Attribute) and
                self.check_attribute(subject.func, lambda x: x in self.channels, 'offer'))

    def function_call(self, call, call_args):
        func_name = call.func.id
        for idx, arg in enumerate(call_args):
            if isinstance(arg, ast.Name) and arg.id in self.channels:
                # external function, f(ch)
                func = self.functions[func_name]
                # channel name where the function was called, ch
                main_channel_name = arg.id
                # channel name in called function, ch1
                func_channel_name = func.args.args[idx].arg

                self.channels[func_channel_name] = self.channels[main_channel_name]
                self.verify_channels(func.body)
                self.channels[main_channel_name] = self.channels[func_channel_name]

                if not (main_channel_name == func_channel_name):
                    self.channels.pop(func_channel_name)

    def advance(self, ch_name):
        """
        Advance a session type if it is in
        * global scope : go to right child
        * local scope  : inside a left or right branch, advance left or right branch
        """
        st = self.get_session_type(ch_name)
        if not self.scopes:  # global scope
            self.channels[ch_name] = st.right
        else:  # local scope
            if (self.scopes[len(self.scopes)-1] == Scope.LEFT):
                self.channels[ch_name].left = st.right
            else:
                self.channels[ch_name].right = st.right

            if(self.channels[ch_name].left == None and self.channels[ch_name].right == None):
                self.channels[ch_name] = self.channels[ch_name].right

    def verify_postconditions(self):
        """ 
        If a session-type list is not empty, it has not been used in
        accordance with its type: throw error.  
        """
        errors = []
        for ch_name, ch_ops in self.channels.items():
            if ch_ops:
                errors.append(
                    f'channel "{ch_name}" is not exhausted, missing: {self.channels[ch_name]}')

        if errors:
            raise Exception(f"ill-typed program: {errors}")

    def fail_if_exhausted(self, st, ch_name):
        if not st:
            raise Exception(f"{ch_name} has been exhausted of operations")

    def get_session_type(self, ch_name: str):
        st = self.channels[ch_name]
        for left_right in self.scopes:
            if left_right == Scope.LEFT:
                st = st.left
            else:
                st = st.right
        return st

    def add_scope(self, scope_type: Scope):
        self.scopes.append(scope_type)

    def pop_scope(self):
        return self.scopes.pop()

    def lookup(self, x): 
        return self.env[x]

    def infer(self, expr) -> type:
        # TODO: currently we only support constants, expand with function calls, expressions etc?
        #print('infer')
        #print('current env:', self.env)

        # print(f"argument infered to be type {type(arg)}")
        return type(expr.value) if isinstance(expr, ast.Constant) else self.lookup(expr.id)


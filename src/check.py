import ast
import copy
import inspect
import sys
from ast import *
from functools import reduce
from textwrap import dedent
from types import BuiltinFunctionType, BuiltinMethodType, NoneType

from debug import *
from environment import Environment
from immutable_list import ImmutableList
from lib import *
from statemachine import BranchEdge, STParser, Node, TGoto, Transition
from sessiontype import STR_ST_MAPPING

visited_files: dict[str, object] = {}

Closure = namedtuple('Closure', ['args', 'body'])
ChannelOperation = namedtuple('ChannelOperation', ['ch', 'operation'])


class TypeChecker(NodeVisitor):

    def __init__(self, tree, inside_class=False) -> None:
        self.inside_class = inside_class
        self.subst_var: dict[str, str] = {}
        self.functions_queue: dict[str, FunctionDef] = {}
        self.environments: ImmutableList[Environment] = ImmutableList().add(Environment())
        self.in_functions: ImmutableList[FunctionDef] = ImmutableList()
        self.loop_depth: int = 0  # Not in loop = 0
        self.loop_entrypoints: Set[int] = set()  
        self.loop_breakpoints: Set[int] = set()  
        self.tree = tree


    def run(self):
        self.visit(self.tree)
        self.validate_post_conditions()

    def validate_post_conditions(self):
        latest = self.get_latest_scope()
        failing_channels = []
        for (k, v) in latest.get_vars():
            if isinstance(v, Node):
                if not v.accepting and v.identifier not in self.loop_entrypoints and not v.any_state:
                    err_msg = f'\nchannel <{k}> not exhausted - next up is:'
                    for edge in v.outgoing.keys():
                        err_msg += f'\n- {str(edge)}'
                    failing_channels.append(err_msg)
        if failing_channels:
            msgs = '\n'.join(failing_channels)
            raise SessionException(msgs)

    def is_builtin(self, typ):
        return typ in sys.builtin_module_names or \
               isinstance(typ, BuiltinFunctionType) or \
               isinstance(typ, BuiltinMethodType) or \
               isinstance(typ, ModuleType)
    
    def is_dictionary(self, typ):
        return isinstance(typ, ContainerType) and typ._name == 'Dict'

    def visit_function(self, node: FunctionDef) -> Typ:
        self.in_functions = self.in_functions.add(node)
        expected_return_type: type = self.get_return_type(node)
        params = self.visit(node.args)
        if self.inside_class:
            fail_if(params[0][0] != 'self', "a class function must have self as first parameter")
            params = params[1:]
        params = [(name, (typ if not isinstance(typ, SessionStub) else self.build_session_type(typ.stub))) for
                  (name, typ) in params]
        function_type: ImmutableList[Tuple[str, type]] = \
            ImmutableList(params).map(lambda tp: tp[1]).add(expected_return_type)

        self.get_latest_scope().bind_func(node.name, function_type.items())
        self.dup()
        for (v, t) in params:
            if v not in self.subst_var:
                self.bind_var(v, t)

        self.visit_statements(node.body)
        env = self.pop()
        channels = env.get_kind(Node)
        for var, nd in channels:
            self.bind_var(var, nd)
        self.in_functions = self.in_functions.tail()
        return function_type.items()

    def visit_FunctionDef(self, node: FunctionDef) -> Typ:
        if self.inside_class:
            return
        if node.name not in self.functions_queue:
            self.functions_queue[node.name] = node
            return
        else:
            self.visit_function(node)

    def visit_Compare(self, node: Compare) -> type:
        left = self.lookup_or_self(self.visit(node.left))
        right = self.lookup_or_self(self.visit(node.comparators[0]))
        union(left, right)
        return bool

    def visit_statements(self, stms: List[stmt]):
        current_loop_depth = self.loop_depth
        for stm in stms:
            self.visit(stm)
            if current_loop_depth > self.loop_depth:
                break


    def visit_AugAssign(self, node: AugAssign) -> None:
        debug_print('visit_AugAssign', dump(node))
        target = self.lookup_or_self(self.visit(node.target))
        value = self.lookup_or_self(self.visit(node.value))

        fail_if_cannot_cast(target, value, f"{target} is not compatible with {value}")

    def visit_Match(self, node: ast.Match) -> None:
        debug_print('visit_Match', dump(node))
        subj = self.visit(node.subject)

        if isinstance(subj, Node):
            ch_name = node.subject.func.value.id
            nd = subj
            offers = [key.key for key in nd.outgoing.keys()]
            current_loop_depth = self.loop_depth
            for case in node.cases:
                self.loop_depth = current_loop_depth
                match_value = case.pattern.value
                if isinstance(match_value, Constant):
                    branch_pick = match_value.value
                else:
                    branch_pick = self.visit(match_value)
                self.bind_var(ch_name, nd)
                new_nd = None
                for edge in nd.outgoing:
                    assert isinstance(edge, BranchEdge)
                    if branch_pick == edge.key:
                        if branch_pick not in offers:
                            raise SessionException(f"Case '{branch_pick}' already visited", node)
                        offers.remove(branch_pick)
                        new_nd = nd.outgoing[edge]
                        break
                if new_nd is None:
                    raise SessionException(f"Case option '{ast.unparse(match_value)}' not an available offer")
                self.bind_var(ch_name, new_nd)
                self.visit_statements(case.body)
                self.validate_post_conditions()
            if offers:
                raise SessionException(f"Match cases were not exhaustive; paths not covered: {', '.join(offers)}", node)

        else:
            for case in node.cases:
                self.dup()
                case: ast.match_case = case
                p = self.visit(case.pattern)

                self.bind_var(p, self.lookup_or_self(subj))
                if case.guard:
                    self.visit(case.guard)

                self.visit_statements(case.body)
                self.pop()

    def visit_MatchAs(self, node: ast.MatchAs) -> Union[str, None]:
        return node.name if node.name else None

    def visit_arguments(self, node: arguments) -> list[type]:
        args: ImmutableList[type] = ImmutableList()
        for argument in node.args:
            args = args.add(self.visit_arg(argument))
        return args.items()

    def visit_arg(self, node: arg) -> Tuple[str, type]:
        match node:
            case node if node.annotation:
                ann: Typ = self.visit(node.annotation)
                return node.arg, ann
            case _:
                return node.arg, Any

    def visit_Name(self, node: Name) -> Tuple[str, Typ] | Typ:
        debug_print('visit_Name', dump(node))
        name = node.id
        if name == 'DEBUG':
            return self
        if name in self.subst_var:
            name = self.subst_var[name]
        opt = str_to_typ(name)
        return opt or self.get_latest_scope().lookup_var_or_default(name,
                                                                    self.get_latest_scope().lookup_func_or_default(
                                                                        name, name))

    def visit_Tuple(self, node: ast.Tuple) -> list:
        debug_print('visit_Tuple', dump(node))
        fail_if(not node.elts, "Tuple should contain elements", Exception)
        elements = []
        for el in node.elts:
            # TODO: Hardcoding away forward-refs for now
            if isinstance(el, Name) and el.id.lower() in STR_ST_MAPPING:
                typ = STR_ST_MAPPING[el.id.lower()]
                elements.append(typ)
            else:
                elements.append(self.visit(el))
        return elements

    def visit_List(self, node: ast.List) -> None:
        debug_print('visit_List', dump(node))
        if node.elts:
            list_types: List[Typ] = [self.visit(el) for el in node.elts]
            res = reduce(union, list_types)
            return List[res]
        else:
            return List[Any]

    def visit_Attribute(self, node: Attribute) -> Typ:
        debug_print('attribute', dump(node))
        value = self.visit(node.value)
        attr = node.attr
        if isinstance(value, Node):
            return ChannelOperation(value, attr)
        if value == self:  # TODO: Debug hack from within source
            invokable = getattr(self, attr)
            invokable()
            return
        if value in STR_ST_MAPPING or attr in STR_ST_MAPPING:
            assert value not in STR_ST_MAPPING, "Do we ever expect this?"
            return ChannelOperation(value, attr)
        else:
            if self.is_builtin(value):
                return BuiltinFunctionType
            env = self.get_latest_scope().lookup_nested(value)
            return env.lookup_func(attr)

    def visit_Assign(self, node: Assign) -> None:
        debug_print('visit_Assign', dump(node))
        fail_if(not len(node.targets) == 1, "Assigning multiple variables are not supported", Exception)

        target = self.visit(node.targets[0])

        print('target is', target)
        if is_session_type(node.value):
            self.bind_session_type(node.value, target)
        else:

            value = self.visit(node.value)
            print(ast.unparse(node.value), '->', value)
            if isinstance(node.value, ast.Tuple):
                value = parameterize(Tuple, value)
            if self.is_dictionary(target):
                expected_value = target.__args__[1]
                if value != expected_value:
                    raise StaticTypeError(f'value type of dictionary should be {type_to_str(expected_value)}, got {type_to_str(value)}', node)
            self.bind_var(target, value)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        debug_print('visit_AnnAssign', dump(node))
        target: str = self.visit(node.target)
        print('ann: target is', target)
        if is_session_type(node.value):
            self.bind_session_type(node.value, target)
        else:
            name_or_type = self.visit(node.annotation)
            rhs_type = self.visit(node.value)

            if isinstance(rhs_type, str):
                rhs_type = self.lookup_or_self(rhs_type)
            elif isinstance(name_or_type, typing._GenericAlias) and name_or_type.__origin__ == tuple:
                rhs_type = parameterize(Tuple, rhs_type)

            if is_type(name_or_type):
                self.bind_var(target, union(rhs_type, name_or_type))
            else:
                ann_type: Type = locate(name_or_type)
                fail_if(not type(ann_type) == type, f"{type(ann_type)} did not match {type}", Exception)
                rhs_type: Type = self.visit(node.value)
                fail_if(not ann_type == rhs_type, f'annotated type {ann_type} does not match inferred type {rhs_type}')
                self.bind_var(target, ann_type)

    def visit_BinOp(self, node: BinOp) -> type:
        debug_print('visit_BinOp', dump(node))
        l_typ = self.visit(node.left)
        r_typ = self.visit(node.right)
        try:
            return union(l_typ, r_typ)
        except TypeError as err:
            raise StaticTypeError(err, node)


    def visit_Break(self, node: Break) -> Any:
        if self.loop_depth == 0:
            raise StaticTypeError('call to break outside of loop', node)
        self.loop_depth -= 1
        chans = self.get_latest_scope().get_kind(Node)
        for (_, nd) in chans:
            self.loop_breakpoints.add(nd.identifier)
        

    def visit_Constant(self, node: Constant) -> type:
        return type(node.value)

    def in_function_queue(self, key) -> bool:
        return type(key) is str and key in self.function_queue

    def visit_Lambda(self, node: Lambda) -> Any:
        return Closure(node.args, node.body)

    def call_to_function_affecting_sessiontype(self, node: Call, func_name: str):
        visited_args = [self.visit(arg) for arg in node.args]
        function: FunctionDef = self.functions_queue[func_name]
        if any(isinstance(arg, Node) for arg in visited_args):
            # We passed a channel to a function
            params = self.visit(function.args)
            pre_subst = copy.deepcopy(self.subst_var)
            for (param, typ), (arg_ast, arg) in zip(params, zip(node.args, visited_args)):
                if isinstance(typ, type) and isinstance(arg, type):
                    try:
                        union(typ, arg)
                    except TypeError:
                        raise IllegalArgumentException(
                            f'function <{func_name}> got {param}={type_to_str(arg)} where it expected {param}={type_to_str(typ)}')
                if isinstance(arg, Node):
                    assert isinstance(param, str), "Expecting parameter to be a string"
                    assert isinstance(typ, SessionStub), "Expecting annotated type being a stub"
                    node_stub = self.build_session_type(typ.stub)
                    if arg != node_stub:
                        raise SessionException(f'function <{func_name}> received ill-typed session', node)

                    if isinstance(arg_ast, Name):
                        self.subst_var[param] = arg_ast.id
                    else:
                        unioned = union(typ, arg)
                        self.bind_var(param, unioned)

            self.visit_function(function)
            self.subst_var = pre_subst
            res = self.visit(node.func)
            return res

    def visit_Call(self, node: Call) -> Typ:
        debug_print('visit_Call', dump(node))
        call_func = self.visit(node.func)
        if isinstance(call_func, str):
            match call_func:
                case 'Channel':
                    for arg in node.args:
                        if isinstance(arg, Subscript):
                            return self.build_session_type(arg)
                case 'typecheck_file':
                    return Any
                case _:
                    return self.call_to_function_affecting_sessiontype(node, call_func)

        if isinstance(call_func, Closure):
            visited_args = []
            for arg in node.args:
                visited_args.append(self.visit(arg))
            for (arg, (var, typ)) in zip(visited_args, self.visit(call_func.args)):
                self.bind_var(var, union(arg, typ))

            return self.visit(call_func.body)

        if isinstance(call_func, ChannelOperation):
            args = self.get_function_args(node.args)
            op = call_func[1]
            ch_name = node.func.value.id
            if ch_name in self.subst_var:
                ch_name = self.subst_var[ch_name]
            nd = self.get_latest_scope().try_find(ch_name)
            if nd == Any:
                return Any
            if not nd or nd and not isinstance(nd, Node):
                nd = call_func[0]
            if not nd.outgoing:
                if not nd.any_state:
                    raise SessionException(f'Call to {op} on exhausted channel', node)
                return Any
            out_edge = nd.get_edge()
            if isinstance(out_edge, Transition) and isinstance(out_edge.typ, str):
                aliased_typ = self.lookup_or_self(out_edge.typ)
                assert isinstance(aliased_typ, Typ)
                out_edge.typ = aliased_typ
            match op:
                case 'recv':
                    valid_action, _ = nd.valid_action_type(op, None)
                    if not valid_action:
                        raise SessionException(f'expected {nd.outgoing_action()}, but recv was called', node)
                    next_nd = nd.next_nd()
                    self.bind_var(ch_name, next_nd)
                    return nd.outgoing_type()
                case 'send':
                    argument = args.head()

                    valid_action, valid_typ = nd.valid_action_type(op, argument)

                    if not valid_action:
                        raise SessionException(f'expected a {nd.outgoing_action()}, but send was called', node)
                    elif not valid_typ and argument != NoneType and argument != BuiltinMethodType:
                        raise SessionException(
                            f'expected to send a {type_to_str(nd.outgoing_type())}, got {type_to_str(argument)}', node)
                    next_nd = nd.next_nd()
                    self.bind_var(ch_name, next_nd)
                case 'offer':
                    return nd
                case 'choose':
                    pick = args.head()
                    if isinstance(node.args[0], Constant):
                        pick = node.args[0].value
                    new_nd = None
                    for edge in nd.outgoing:
                        if not isinstance(edge, BranchEdge):
                            raise SessionException(f"choose was called where {edge.action} was expected", node)
                        if pick == edge.key:
                            new_nd = nd.outgoing[edge]
                            break
                    if not new_nd:
                        options = ', '.join(k.key for k in nd.outgoing.keys())
                        raise SessionException(f"The choice of '{pick}' is not one of: {options}", node)
                    if new_nd.outgoing and isinstance(new_nd.get_edge(), TGoto):
                        new_nd = new_nd.next_nd()
                    self.bind_var(ch_name, new_nd)
                    return nd

        elif isinstance(call_func, FunctionTyp):
            provided_args = self.get_function_args(node.args)
            contains_bound_channel = \
                any(isinstance(x, Name) for x in node.args) and \
                any(isinstance(x, Node) for x in provided_args)
            if contains_bound_channel:
                name = node.func.id
                assert isinstance(name, str), "Expecting call to a function"
                return self.call_to_function_affecting_sessiontype(node, name)
            signature = ImmutableList(call_func)
            return_type = signature.last()
            call_func = signature.discard_last()
            func_name = node.func.attr if isinstance(node.func, Attribute) else node.func.id
            self.compare_function_arguments_and_parameters(func_name, provided_args, call_func)
            return return_type
        elif isinstance(call_func, BuiltinFunctionType):
            args = [self.visit(arg) for arg in node.args]
        return call_func

    def visit_JoinedStr(self, _: JoinedStr) -> Any:
        return str

    def visit_ClassDef(self, node: ClassDef) -> None:
        debug_print('visit_ClassDef', dump(node))

        self.dup()

        self.inside_class = True
        self.visit(Module(node.body))
        self.inside_class = False
        env = self.pop()

        self.get_latest_scope().bind_nested(node.name, env)

    def visit_While(self, node: While) -> None:
        debug_print('visit_While', dump(node))
        self.loop_depth += 1
        self.validate_loop(node)

    def visit_For(self, node: For) -> None:
        debug_print('visit_For', dump(node))
        self.loop_depth += 1
        target = self.visit(node.target)
        ite = self.visit(node.iter)
        typ = ite.__args__[0] if isinstance(ite, ContainerType) else str
        self.bind_var(target, typ)

        self.validate_loop(node)

    def visit_Dict(self, node: Dict) -> Dict[Typ, Typ]:
        debug_print('visit_Dict', dump(node))
        key_typ = reduce(union, ((self.visit(k)) for k in node.keys)) if node.keys else Any
        val_typ = reduce(union, ((self.visit(v)) for v in node.values)) if node.values else Any
        if isinstance(val_typ, list):
            val_typ = parameterize(Tuple, val_typ)
        res = Dict[key_typ, val_typ]
        return res

    def visit_Subscript(self, node: Subscript) -> Any:
        debug_print('visit_Subscript', dump(node))
        name = node.value.id.lower()
        if name in STR_ST_MAPPING:
            str_repr = self.process_and_substitute(node)
            if name == 'channel':
                return self.build_session_type(str_repr)
            return SessionStub(str_repr)
        else:
            name = self.lookup_or_self(name)
            if isinstance(name, str):
                container = str_to_typ(name)
                types = self.visit(node.slice)
                if isinstance(types, type | list):
                    return parameterize(to_typing(container), types)
                else:
                    return to_typing(container)[types]
            else:
                lookup_able = name
                assert isinstance(lookup_able, ContainerType)
                if self.is_dictionary(lookup_able):
                    key_typ = self.visit(node.slice)
                    if key_typ == NoneType:
                        return Any
                    elif isinstance(key_typ, str):
                        key_typ = self.lookup_or_self(key_typ)
                    kv = lookup_able.__args__
                    if kv[0] == key_typ:
                        return Dict[kv[0], kv[1]]
                    else:
                        raise StaticTypeError(
                            f'dictionary got key of type {type_to_str(key_typ)} where {type_to_str(kv[0])} was expected', node)

    def visit_Return(self, node: Return) -> Any:
        debug_print('visit_Return', dump(node))

        return_type = self.visit(node.value)

        return self.compare_type_to_latest_func_return_type(return_type)

    def visit_If(self, node: If) -> None:
        debug_print('visit_If', dump(node))

        self.visit(node.test)
        self.dup()
        current_loop_depth = self.loop_depth
        self.visit_statements(node.body)
        env_if = self.pop()
        channels: list[(str, Node)] = env_if.get_kind(Node)
        self.loop_depth = current_loop_depth
        then_breakpoints = copy.deepcopy(self.loop_breakpoints)
        self.loop_breakpoints.clear()
        if node.orelse:
            self.dup()
            self.visit_statements(node.orelse)
            env_else = self.pop()
            chans1 = env_else.get_kind(Node)
            for (ch1, nd1), (ch2, nd2) in zip(channels, chans1):
                # This is the scenario after and if-then-else block
                valid = nd1.accepting and nd2.accepting or nd1.identifier == nd2.identifier
                if ch1 == ch2 and not valid:
                    raise SessionException(f'after conditional block, channel <{ch1}> ended up in two different states', node)
        elif channels:
            latest = self.get_latest_scope()
            for (ch, nd) in channels:
                ch1 = latest.lookup_var(ch)
                if nd.identifier != ch1.identifier:
                    raise SessionException('then-block without else should not affect any session types', node)
        self.loop_breakpoints = self.loop_breakpoints.intersection(then_breakpoints)
        self.loop_depth = current_loop_depth
        for (ch, nd) in channels:
            self.bind_var(ch, nd)

    def compare_function_arguments_and_parameters(self, func_name, arguments: ImmutableList, parameters: ImmutableList):
        fail_if(not len(arguments) == len(parameters),
                f'function {func_name} expected {len(parameters)} argument{"s" if len(parameters) > 1 else ""} got {len(arguments)}')
        for actual_type, expected_type in zip(arguments.items(), parameters.items()):
            if isinstance(expected_type, str):  # alias
                _, expected_type = self.get_latest_scope().lookup(expected_type)

            types_differ: bool = expected_type != actual_type
            can_upcast: bool = actual_type == expected_type or can_upcast_to(actual_type, expected_type)
            fail_if(types_differ and not can_upcast,
                    f'function <{func_name}> expected {parameters}, got {arguments}')

    def validate_loop(self, node: While | For):
        pre_channels = self.get_latest_scope().get_kind(Node)
        if pre_channels:
            nds = [chs[1] for chs in pre_channels]
            for nd in nds:
                self.loop_entrypoints.add(nd.identifier)
            pre_channels = nds
        if isinstance(node, While):
            self.visit(node.test)
        self.visit_statements(node.body)
        post_channels = self.get_latest_scope().get_kind(Node)
        if pre_channels and post_channels:
            post_channels = [chs[1] for chs in post_channels]
            for post_chan in post_channels:
                chan_id = post_chan.identifier
                if chan_id not in self.loop_entrypoints and chan_id not in self.loop_breakpoints:
                    raise SessionException(
                        f'loop error: needs to {post_chan.outgoing_action()()} {post_chan.outgoing_type()}', node)

    def process_and_substitute(self, node):
        alias_opts = self.get_latest_scope().get_kind(str)
        stubs = self.get_latest_scope().get_kind(SessionStub)
        channel_str = ast.unparse(node) if isinstance(node, Subscript) else node  # 'Channel[Send[..., <Alias>]]'
        assert isinstance(channel_str, str)
        for key, val in alias_opts:
            assert False, "Remove last: Do we ever run this?"
            channel_str = channel_str.replace(key, val)
        for key, val in stubs:
            channel_str = channel_str.replace(key, val.stub)
        return channel_str

    def build_session_type(self, node):
        channel_str = self.process_and_substitute(node)
        return STParser(src=channel_str).build()

    def bind_session_type(self, node, target):
        nd = self.build_session_type(node)
        self.bind_var(target, nd)

    def compare_type_to_latest_func_return_type(self, return_type: Typ):
        expected_return_type = self.get_current_function_return_type()
        fail_if_cannot_cast(return_type, expected_return_type,
                            f'return type {return_type} did not match {expected_return_type}')
        return return_type

    def get_return_type(self, node: FunctionDef):
        return self.visit(node.returns) if node.returns else Any

    def get_function_args(self, args) -> ImmutableList:
        return ImmutableList([self.visit(arg) for arg in args])

    def push(self) -> None:
        self.environments = self.environments.add(Environment())

    def dup(self) -> None:
        prev_env = copy.deepcopy(self.get_latest_scope())
        self.environments = self.environments.add(prev_env)

    def pop(self) -> Environment:
        latest_scope = self.get_latest_scope()
        self.environments = self.environments.discard_last()
        return latest_scope

    def get_latest_scope(self) -> Environment:
        return self.environments.last()

    def get_current_function_return_type(self):
        current_function: FunctionDef = self.in_functions.last()
        ty = self.get_return_type(current_function)
        return ty

    def lookup_or_self(self, k):
        return self.get_latest_scope().lookup_or_default(k, k)

    def bind_var(self, var: str, typ: Typ) -> None:
        debug_print(f'bind_var: binding {var} to {typ}')
        self.get_latest_scope().bind_var(var, typ)

    def print_envs(self, opt_title='') -> None:
        if opt_title:
            print(opt_title)
        i = 0
        for env in self.environments.items():
            print(f'Env #{i}:', env)
            i += 1
        print('Subst:', self.subst_var)


def is_session_type(node: expr) -> bool:
    def check_subscript(node) -> bool:
        return isinstance(node, Subscript) and isinstance(node.value, Name) and node.value.id == 'Channel'

    return isinstance(node, Call) and check_subscript(node.func)


def typechecker_from_path(file) -> TypeChecker:
    if file in visited_files:
        return visited_files[file]
    src = read_src_from_file(file)
    tree = parse(src)
    tc = TypeChecker(tree)
    tc.run()
    visited_files[file] = tc
    return tc


def typecheck_file():
    return typechecker_from_path(sys.argv[0])

def typecheck_function(function_def):
    function_src: str = dedent(inspect.getsource(function_def))
    module: Module = ast.parse(function_src)
    assert len(module.body) == 1, "Only expecting one element: a FunctionDef"
    function_ast = module.body[0]
    assert isinstance(function_ast, FunctionDef), "Decorator called on non-FunctionDef"
    typechecker: TypeChecker = TypeChecker(function_ast)
    typechecker.run()
    return function_def


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expected 1 argument, got 0')
        sys.exit()
    else:
        typechecker_from_path(sys.argv[1])

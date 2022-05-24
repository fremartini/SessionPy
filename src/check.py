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
from statemachine import BranchEdge, STParser, State, TGoto, Transition
from sessiontype import STR_ST_MAPPING

Closure = namedtuple('Closure', ['args', 'body'])
EndpointOperation = namedtuple('EndpointOperation', ['ch', 'operation'])


class TypeChecker(NodeVisitor):

    def __init__(self, tree, inside_class=False) -> None:
        self.inside_class = inside_class
        self.subst_var: dict[str, str] = {}
        self.functions_queue: dict[str, FunctionDef] = {}
        self.environments: ImmutableList[Environment] = ImmutableList().add(Environment())
        self.in_functions: ImmutableList[FunctionDef] = ImmutableList()
        self.tree = tree

    def run(self):
        self.visit(self.tree)
        self.validate_post_conditions()

    def env(self) -> Environment:
        return self.environments.last()

    def validate_post_conditions(self):
        env = self.env()
        failing_endpoints = []
        for (k, v) in env.get_vars():
            if isinstance(v, State):
                if not v.accepting and v.identifier not in env.loop_entrypoints and not v.any_state:
                    err_msg = f'\nendpoint <{k}> not exhausted - next up is:'
                    for edge in v.outgoing.keys():
                        err_msg += f'\n- {str(edge)}'
                    failing_endpoints.append(err_msg)
        expect(not failing_endpoints, '\n'.join(failing_endpoints))
        if failing_endpoints:
            msgs = '\n'.join(failing_endpoints)
            raise SessionException(msgs)

    def process_function(self, node: FunctionDef) -> Typ:
        self.in_functions = self.in_functions.add(node)
        expected_return_type: type = self.get_return_type(node)
        params = self.visit(node.args)
        if self.inside_class:
            expect(params[0][0] == 'self', "a class function must have self as first parameter", node, StaticTypeError)
            params = params[1:]
        params = [(name, (typ if not isinstance(typ, SessionStub) else self.build_session_type(typ.stub))) for
                  (name, typ) in params]
        function_type: ImmutableList[Tuple[str, type]] = \
            ImmutableList(params).map(lambda tp: tp[1]).add(expected_return_type)

        self.env().bind_func(node.name, function_type.items())
        self.dup()
        for (v, t) in params:
            if v not in self.subst_var:
                self.env().bind_var(v, t)

        self.visit_statements(node.body)
        endpoints = self.pop().get_kind(State)
        for var, current_state in endpoints:
            self.env().bind_var(var, current_state)
        self.in_functions = self.in_functions.tail()
        return function_type.items()

    def visit_statements(self, statements: List[stmt]):
        current_loop_depth = self.env().loop_depth
        for stm in statements:
            self.visit(stm)
            if current_loop_depth > self.env().loop_depth:
                break

    def visit_arguments(self, node: arguments) -> list[type]:
        args: ImmutableList[type] = ImmutableList()
        for argument in node.args:
            args = args.add(self.process_arg(argument))
        return args.items()

    def process_arg(self, node: arg) -> Tuple[str, type]:
        match node:
            case node if node.annotation:
                ann: Typ = self.visit(node.annotation)
                return node.arg, ann
            case _:
                return node.arg, Any

    def call_to_function_affecting_sessiontype(self, node: Call, func_name: str):
        visited_args = [self.visit(a) for a in node.args]
        function: FunctionDef = self.functions_queue[func_name]
        args_contain_sessiontype = any(isinstance(a, State) for a in visited_args)
        if args_contain_sessiontype:
            # We passed an endpoint to a function
            params = self.visit(function.args)
            pre_subst = copy.deepcopy(self.subst_var)
            for (param, typ), (arg_ast, arg) in zip(params, zip(node.args, visited_args)):
                if isinstance(typ, type) and isinstance(arg, type):
                    try:
                        union(typ, arg)
                    except TypeError:
                        raise IllegalArgumentException(
                            f'function <{func_name}> got {param}={type_to_str(arg)} where it expected {param}={type_to_str(typ)}')
                if isinstance(arg, State):
                    expect(isinstance(param, str), f"Expecting parameter to be a string, got {param}",
                           node, StaticTypeError)
                    expect(isinstance(typ, SessionStub), f"Expecting annotated type being a stub, got {typ}",
                           node)
                    node_stub = self.build_session_type(typ.stub)
                    expect(arg == node_stub, f'function <{func_name}> received ill-typed session', node)
                    if isinstance(arg_ast, Name):
                        self.subst_var[param] = arg_ast.id
                    else:
                        unified = union(typ, arg)
                        self.env().bind_var(param, unified)

            self.process_function(function)
            self.subst_var = pre_subst
            res = self.visit(node.func)
            return res

    def compare_function_arguments_and_parameters(self, func_name, arguments: ImmutableList, parameters: ImmutableList):
        err_msg = f'function <{func_name}> expected {len(parameters)} argument(s) got {len(arguments)}'
        expect(len(arguments) == len(parameters), err_msg, exc=StaticTypeError)
        for actual_type, expected_type in zip(arguments.items(), parameters.items()):
            if isinstance(expected_type, str):  # alias
                _, expected_type = self.env().lookup(expected_type)

            types_differ: bool = expected_type != actual_type
            can_upcast: bool = actual_type == expected_type or expected_type == Any
            expect(not types_differ and can_upcast,
                   f'function <{func_name}> expected {parameters}, got {arguments}', exc=StaticTypeError)

    def validate_loop(self, node: While | For):
        pre_endpoints = self.env().get_kind(State)
        if pre_endpoints:
            nds = [chs[1] for chs in pre_endpoints]
            for current_state in nds:
                self.env().loop_entrypoints.add(current_state.identifier)
            pre_endpoints = nds
        if isinstance(node, While):
            self.visit(node.test)
        self.visit_statements(node.body)
        post_endpoints = self.env().get_kind(State)
        if pre_endpoints and post_endpoints:
            post_endpoints = [chs[1] for chs in post_endpoints]
            for post_chan in post_endpoints:
                chan_id = post_chan.identifier
                expect(chan_id in self.env().loop_entrypoints or chan_id in self.env().loop_breakpoints,
                       f'loop error: needs to {post_chan}')

    def process_and_substitute(self, node):
        stubs = self.env().get_kind(SessionStub)
        endpoint_str = ast.unparse(node) if isinstance(node, Subscript) else node  # 'Endpoint[Send[..., <Alias>]]'
        expect(isinstance(endpoint_str, str), f"Expected unparsed node, or parsed node, to be of string type, got '{endpoint_str}'", node, UnexpectedInternalBehaviour)
        for key, val in stubs:
            endpoint_str = endpoint_str.replace(key, val.stub)
        return endpoint_str

    def build_session_type(self, node):
        endpoint_str = self.process_and_substitute(node)
        return STParser(src=endpoint_str).build()

    def bind_session_type(self, node, target):
        current_state = self.build_session_type(node)
        self.env().bind_var(target, current_state)

    def compare_type_to_latest_func_return_type(self, return_type: Typ):
        expected_return_type = self.get_current_function_return_type()
        fail_if_cannot_cast(return_type, expected_return_type,
                            f'return type {return_type} did not match {expected_return_type}')
        return return_type

    def get_return_type(self, node: FunctionDef):
        return self.visit(node.returns) if node.returns else Any

    def get_function_args(self, args) -> ImmutableList:
        return ImmutableList([self.visit(arg) for arg in args])

    def get_current_function_return_type(self):
        current_function: FunctionDef = self.in_functions.last()
        ty = self.get_return_type(current_function)
        return ty

    def process_session_operation(self, node: Call, ch_op: EndpointOperation):
        args = self.get_function_args(node.args)
        op = ch_op.operation
        ch_name = node.func.value.id
        if ch_name in self.subst_var:
            ch_name = self.subst_var[ch_name]
        current_state = self.env().try_find(ch_name)
        if current_state == Any:
            return Any
        if not current_state or current_state and not isinstance(current_state, State):
            current_state = ch_op.ch
        if not current_state.outgoing:
            expect(current_state.any_state, f'Call to {op} on exhausted endpoint', node)
            return Any
        out_edge = current_state.get_edge()
        if isinstance(out_edge, Transition) and isinstance(out_edge.typ, str):
            aliased_typ = self.env().lookup_or_self(out_edge.typ)
            expect(isinstance(aliased_typ, Typ), f"aliased type in transition should be a Typ, got {aliased_typ}",
                   node, UnexpectedInternalBehaviour)
            out_edge.typ = aliased_typ
        res = Any
        match op:
            case 'recv':
                valid_action, _ = current_state.valid_action_type(op, None)
                expect(valid_action, f'expected {current_state.outgoing_action()}, but recv was called', node)
                next_nd = current_state.next_nd()
                self.env().bind_var(ch_name, next_nd)
                res = current_state.outgoing_type()
            case 'send':
                argument = args.head()
                valid_action, valid_typ = current_state.valid_action_type(op, argument)
                expect(valid_action, f'expected a {current_state.outgoing_action()}, but send was called', node)
                valid_condition = valid_typ or argument == NoneType or is_builtin_or_module_type(argument)
                expect(valid_condition,
                       f'expected to send a {type_to_str(current_state.outgoing_type())}, got {type_to_str(argument)}',
                       node)
                next_nd = current_state.next_nd()
                self.env().bind_var(ch_name, next_nd)
            case 'offer':
                res = current_state
            case 'choose':
                pick = args.head()
                if isinstance(node.args[0], Constant):
                    pick = node.args[0].value
                new_nd = None
                for edge in current_state.outgoing:
                    if pick == edge.key:
                        new_nd = current_state.outgoing[edge]
                        break
                if not new_nd:
                    options = ', '.join(k.key for k in current_state.outgoing.keys())
                    expect(new_nd, f"The choice of '{pick}' is not one of: {options}", node)
                if new_nd.outgoing and isinstance(new_nd.get_edge(), TGoto):
                    new_nd = new_nd.next_nd()
                self.env().bind_var(ch_name, new_nd)
                res = current_state
        return res

    """ ################### """
    # ENVIRONMENT HELPERS #
    """ ################### """

    def push(self) -> None:
        self.environments = self.environments.add(Environment())

    def dup(self) -> None:
        prev_env = copy.deepcopy(self.env())
        self.environments = self.environments.add(prev_env)

    def pop(self) -> Environment:
        latest_scope = self.env()
        self.environments = self.environments.discard_last()
        return latest_scope

    def print_envs(self, opt_title='') -> None:
        if opt_title:
            print(opt_title)
        i = 0
        for env in self.environments.items():
            print(f'Env #{i}:', env)
            i += 1
        print('Subst:', self.subst_var)

    """ ##################### """
    # VISITOR PATTERN BELOW #
    """ ##################### """

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        debug_print('visit_AnnAssign', dump(node))
        target: str = self.visit(node.target)
        if is_session_type(node.value):
            self.bind_session_type(node.value, target)
        else:
            name_or_type = self.visit(node.annotation)
            rhs_type = self.visit(node.value)

            if isinstance(rhs_type, str):
                rhs_type = self.env().lookup_or_self(rhs_type)
            elif isinstance(name_or_type, typing._GenericAlias) and name_or_type.__origin__ == tuple:
                rhs_type = parameterize(Tuple, rhs_type)

            if is_type(name_or_type):
                self.env().bind_var(target, union(rhs_type, name_or_type))
            else:
                ann_type: object = locate(name_or_type)
                expect(type(ann_type) == type, f"{type(ann_type)} did not match {type}", Exception)
                rhs_type: Type = self.visit(node.value)
                expect(ann_type == rhs_type, f'annotated type {ann_type} does not match inferred type {rhs_type}')
                self.env().bind_var(target, ann_type)

    def visit_Assign(self, node: Assign) -> None:
        debug_print('visit_Assign', dump(node))
        expect(len(node.targets) == 1, "Assigning multiple variables are not supported", Exception)

        target = self.visit(node.targets[0])

        if is_session_type(node.value):
            self.bind_session_type(node.value, target)
        else:
            value = self.visit(node.value)
            if isinstance(node.value, ast.Tuple):
                value = parameterize(Tuple, value)
            self.env().bind_var(target, value)

    def visit_Attribute(self, node: Attribute) -> Typ:
        debug_print('attribute', dump(node))
        value = self.visit(node.value)
        attr = node.attr
        if isinstance(value, State):
            return EndpointOperation(value, attr)
        if value in STR_ST_MAPPING or attr in STR_ST_MAPPING:
            return EndpointOperation(value, attr)
        else:
            if is_builtin_or_module_type(value):
                return BuiltinFunctionType
            env = self.env().lookup_nested(value)
            return env.lookup_func(attr)

    def visit_AugAssign(self, node: AugAssign) -> None:
        debug_print('visit_AugAssign', dump(node))
        target = self.env().lookup_or_self(self.visit(node.target))
        value = self.env().lookup_or_self(self.visit(node.value))
        fail_if_cannot_cast(target, value, f"{target} is not compatible with {value}")

    def visit_BinOp(self, node: BinOp) -> type:
        debug_print('visit_BinOp', dump(node))
        l_typ = self.visit(node.left)
        r_typ = self.visit(node.right)
        try:
            return union(l_typ, r_typ)
        except TypeError as err:
            raise StaticTypeError(err.__str__(), node)

    def visit_Break(self, node: Break) -> Any:
        expect(self.env().loop_depth != 0, 'call to break outside of loop', node, StaticTypeError)
        self.env().loop_depth -= 1
        endpoints = self.env().get_kind(State)
        for (_, current_state) in endpoints:
            self.env().loop_breakpoints.add(current_state.identifier)

    def visit_Call(self, node: Call) -> Typ:
        debug_print('visit_Call', dump(node))
        call_func = self.visit(node.func)
        if isinstance(call_func, str):
            match call_func:
                case 'Endpoint':
                    for arg in node.args:
                        if isinstance(arg, Subscript):
                            return self.build_session_type(arg)
                case 'typecheck_file':
                    return Any
                case _:
                    return self.call_to_function_affecting_sessiontype(node, call_func)

        if isinstance(call_func, Closure):
            visited_args = []
            for a in node.args:
                visited_args.append(self.visit(a))
            for (a, (var, typ)) in zip(visited_args, self.visit(call_func.args)):
                self.env().bind_var(var, union(a, typ))
            return self.visit(call_func.body)

        if isinstance(call_func, EndpointOperation):
            return self.process_session_operation(node, call_func)

        elif isinstance(call_func, FunctionTyp):
            provided_args = self.get_function_args(node.args)
            contains_bound_endpoint = \
                any(isinstance(x, Name) for x in node.args) and \
                any(isinstance(x, State) for x in provided_args)
            if contains_bound_endpoint:
                name = node.func.id
                expect(isinstance(name, str), f"Expecting call to a function, got {name}", node,
                       UnexpectedInternalBehaviour)
                return self.call_to_function_affecting_sessiontype(node, name)
            signature = ImmutableList(call_func)
            return_type = signature.last()
            call_func = signature.discard_last()
            func_name = node.func.attr if isinstance(node.func, Attribute) else node.func.id
            self.compare_function_arguments_and_parameters(func_name, provided_args, call_func)
            return return_type
        elif is_builtin_or_module_type(call_func):
            for a in node.args:
                self.visit(a)
        return call_func

    def visit_ClassDef(self, node: ClassDef) -> None:
        debug_print('visit_ClassDef', dump(node))
        self.dup()
        self.inside_class = True
        self.visit(Module(node.body))
        self.inside_class = False
        env = self.pop()
        self.env().bind_nested(node.name, env)

    def visit_Compare(self, node: Compare) -> type:
        left = self.env().lookup_or_self(self.visit(node.left))
        right = self.env().lookup_or_self(self.visit(node.comparators[0]))
        try:
            union(left, right)
        except TypeError:
            raise StaticTypeError(f'cannot compare {left} and {right}', node)
        return bool

    def visit_Constant(self, node: Constant) -> type:
        return type(node.value)

    def visit_Dict(self, node: Dict) -> Dict[Typ, Typ]:
        debug_print('visit_Dict', dump(node))
        key_typ = reduce(union, ((self.visit(k)) for k in node.keys)) if node.keys else Any
        val_typ = reduce(union, ((self.visit(v)) for v in node.values)) if node.values else Any
        if isinstance(val_typ, list):
            val_typ = parameterize(Tuple, val_typ)
        res = Dict[key_typ, val_typ]
        return res

    def visit_For(self, node: For) -> None:
        debug_print('visit_For', dump(node))
        self.env().loop_depth += 1
        target = self.visit(node.target)
        ite = self.visit(node.iter)
        typ = ite.__args__[0] if is_container(ite) else str
        self.env().bind_var(target, typ)
        self.validate_loop(node)

    def visit_FunctionDef(self, node: FunctionDef) -> Typ:
        if self.inside_class:
            return
        if node.name not in self.functions_queue:
            self.functions_queue[node.name] = node
            return
        else:
            self.process_function(node)

    def visit_If(self, node: If) -> None:
        debug_print('visit_If', dump(node))

        self.visit(node.test)
        self.dup()
        current_loop_depth = self.env().loop_depth
        self.visit_statements(node.body)
        env_if = self.pop()
        endpoints: list[(str, State)] = env_if.get_kind(State)
        self.env().loop_depth = current_loop_depth
        then_breakpoints = copy.deepcopy(self.env().loop_breakpoints)
        self.env().loop_breakpoints.clear()
        if node.orelse:
            self.dup()
            self.visit_statements(node.orelse)
            env_else = self.pop()
            chans1: list[tuple[str, State]] = env_else.get_kind(State)
            for (ch1, nd1), (ch2, nd2) in zip(endpoints, chans1):
                # This is the scenario after and if-then-else block
                valid = nd1.accepting and nd2.accepting or nd1.identifier == nd2.identifier
                expect(ch1 != ch2 or valid,
                       f'after conditional block, endpoint <{ch1}> ended up in two different states',
                       node)
        elif endpoints:
            latest = self.env()
            for (ch, current_state) in endpoints:
                ch1 = latest.lookup_var(ch)
                expect(current_state.identifier == ch1.identifier, 'then-block without else should not affect any session types', node)
        self.env().loop_breakpoints = self.env().loop_breakpoints.intersection(then_breakpoints)
        self.env().loop_depth = current_loop_depth
        for (ch, current_state) in endpoints:
            self.env().bind_var(ch, current_state)

    def visit_JoinedStr(self, _: JoinedStr) -> Any:
        return str

    def visit_Lambda(self, node: Lambda) -> Any:
        return Closure(node.args, node.body)

    def visit_List(self, node: ast.List) -> None:
        debug_print('visit_List', dump(node))
        res = Any
        if node.elts:
            list_types: List[Typ] = [self.visit(el) for el in node.elts]
            res = reduce(union, list_types)
        return List[res]

    def visit_Match(self, node: ast.Match) -> None:
        debug_print('visit_Match', dump(node))
        subj = self.visit(node.subject)

        if isinstance(subj, State):
            ch_name = node.subject.func.value.id
            current_state = subj
            offers = [key.key for key in current_state.outgoing.keys()]
            current_loop_depth = self.env().loop_depth
            for case in node.cases:
                self.env().loop_depth = current_loop_depth
                match_value = case.pattern.value
                if isinstance(match_value, Constant):
                    branch_pick = match_value.value
                else:
                    branch_pick = self.visit(match_value)
                self.env().bind_var(ch_name, current_state)
                new_nd = None
                for edge in current_state.outgoing:
                    expect(isinstance(edge, BranchEdge),
                           f"Outgoing edges should be BranchEdges, got {edge}",
                           node, UnexpectedInternalBehaviour)
                    if branch_pick == edge.key:
                        expect(branch_pick in offers,
                               f"Case '{branch_pick}' already visited",
                               node)
                        offers.remove(branch_pick)
                        new_nd = current_state.outgoing[edge]
                        break
                expect(new_nd, f"Case option '{ast.unparse(match_value)}' not an available offer", node)
                self.env().bind_var(ch_name, new_nd)
                self.visit_statements(case.body)
                self.validate_post_conditions()

            expect(not offers, f"Match cases were not exhaustive; paths not covered: {', '.join(offers)}", node)

        else:
            for mc in node.cases:
                self.dup()
                mc: ast.match_case = mc
                p = self.visit(mc.pattern)

                self.env().bind_var(p, self.env().lookup_or_self(subj))
                if mc.guard:
                    self.visit(mc.guard)

                self.visit_statements(mc.body)
                self.pop()

    def visit_MatchAs(self, node: ast.MatchAs) -> Union[str, None]:
        return node.name if node.name else None

    def visit_Name(self, node: Name) -> Tuple[str, Typ] | Typ:
        debug_print('visit_Name', dump(node))
        name = node.id
        if name in self.subst_var:
            name = self.subst_var[name]
        opt = str_to_typ(name)
        var_or_none = self.env().lookup_var_or_default(name, None)
        fun_or_none = self.env().lookup_func_or_default(name, None)
        return opt or var_or_none or fun_or_none or name

    def visit_Return(self, node: Return) -> Any:
        debug_print('visit_Return', dump(node))
        return_type = self.visit(node.value)
        return self.compare_type_to_latest_func_return_type(return_type)

    def visit_Subscript(self, node: Subscript) -> Any:
        debug_print('visit_Subscript', dump(node))
        name = node.value.id.lower()
        if name in STR_ST_MAPPING:
            str_repr = self.process_and_substitute(node)
            if name == 'endpoint':
                return self.build_session_type(str_repr)
            return SessionStub(str_repr)
        else:
            name = self.env().lookup_or_self(name)
            if isinstance(name, str):
                container = str_to_typ(name)
                types = self.visit(node.slice)
                if isinstance(types, type | list):
                    return parameterize(to_typing(container), types)
                else:
                    return to_typing(container)[types]
            else:
                lookup_able = name
                expect(is_container(lookup_able),
                       f"Subscript annotation only allowed on container/subscript types",
                       node, UnexpectedInternalBehaviour)
                if is_dictionary(lookup_able):
                    key_typ = self.visit(node.slice)
                    if key_typ == NoneType:
                        return Any
                    elif isinstance(key_typ, str):
                        key_typ = self.env().lookup_or_self(key_typ)
                    kv = lookup_able.__args__
                    expect(kv[0] == key_typ,
                           f'dictionary got key of type {type_to_str(key_typ)} where {type_to_str(kv[0])} was expected',
                           node, StaticTypeError)
                    return Dict[kv[0], kv[1]]

    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        return self.visit(node.operand)

    def visit_Tuple(self, node: ast.Tuple) -> list:
        debug_print('visit_Tuple', dump(node))
        expect(node.elts, "Tuple should contain elements", Exception)
        elements = []
        for el in node.elts:
            # TODO: Hardcoding away forward-refs for now
            if isinstance(el, Name) and el.id.lower() in STR_ST_MAPPING:
                typ = STR_ST_MAPPING[el.id.lower()]
                elements.append(typ)
            else:
                elements.append(self.visit(el))
        return elements

    def visit_While(self, node: While) -> None:
        debug_print('visit_While', dump(node))
        self.env().loop_depth += 1
        self.validate_loop(node)


visited_files: dict[str, object] = {}


def is_builtin_or_module_type(typ):
    return typ in sys.builtin_module_names or \
           isinstance(typ, BuiltinFunctionType) or \
           isinstance(typ, BuiltinMethodType) or \
           isinstance(typ, ModuleType)


def is_container(typ: Typ) -> bool:
    return isinstance(typ, ContainerType) and not isinstance(typ, Closure | EndpointOperation)


def is_dictionary(typ: Typ):
    return is_container(typ) and typ._name == 'Dict'


def is_session_type(node: expr) -> bool:
    def check_subscript(node) -> bool:
        return isinstance(node, Subscript) and isinstance(node.value, Name) and node.value.id == 'Endpoint'

    return isinstance(node, Call) and check_subscript(node.func)


def typechecker_from_path(file) -> object | TypeChecker:
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
    expect(len(module.body) == 1,
           "Only expecting one element: a FunctionDef",
           function_def, UnexpectedInternalBehaviour)
    function_ast = module.body[0]
    expect(isinstance(function_ast, FunctionDef),
           "Decorator called on non-FunctionDef",
           function_def, UnexpectedInternalBehaviour)
    typechecker: TypeChecker = TypeChecker(function_ast)
    typechecker.run()
    return function_def


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expected 1 argument, got 0')
        sys.exit()
    else:
        typechecker_from_path(sys.argv[1])

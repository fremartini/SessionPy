import ast
from collections import namedtuple
import copy
import sys
from ast import *
from functools import reduce
from types import NoneType

from debug import *
from environment import Environment
from immutable_list import ImmutableList
from lib import *
from statemachine import BranchEdge, STParser, Node, TGoto, Transition
from sessiontype import STR_ST_MAPPING, SessionException

visited_files: dict[str, object] = {}

Closure = namedtuple('Closure', ['args', 'body'])
ChannelOperation = namedtuple('ChannelOperation', ['ch', 'operation'])
SessionStub = namedtuple('SessionStub', 'stub')


class TypeChecker(NodeVisitor):

    def __init__(self, tree, inside_class=False) -> None:
        self.inside_class = inside_class
        self.subst_var: dict[str, str] = {}
        self.functions_queue: dict[str, FunctionDef] = {}
        self.environments: ImmutableList[Environment] = ImmutableList().add(Environment())
        self.in_functions: ImmutableList[FunctionDef] = ImmutableList()
        self.loop_entrypoints: Set[int] = set()  # TODO: consider putting into environment
        self.visit(tree)
        self.validate_postcondition()

    def validate_postcondition(self):
        latest = self.get_latest_scope()
        failing_chans = []
        for (k,v) in latest.get_vars():
            if isinstance(v, Node):
                if not v.accepting and v.identifier not in self.loop_entrypoints:
                    err_msg = f'\nchannel <{k}> not exhausted - next up is:'
                    for edge in v.outgoing.keys():
                        err_msg += f'\n- {str(edge)}'
                    failing_chans.append(err_msg)
        if failing_chans:
            msgs = '\n'.join(failing_chans)
            raise SessionException(msgs)

    def visit_function(self, node: FunctionDef) -> Typ:
        self.in_functions = self.in_functions.add(node)
        expected_return_type: type = self.get_return_type(node)
        params = self.visit(node.args)
        if self.inside_class:
            fail_if(params[0][0] != 'self', "a class function must have self as first parameter")
            params = params[1:]
        params = [(name,(typ if not isinstance(typ, SessionStub) else STParser(src=typ.stub).build())) for (name,typ) in params]
        function_type: ImmutableList[Tuple[str, type]] = \
            ImmutableList.of_list(params).map(lambda tp: tp[1]).add(expected_return_type)

        self.get_latest_scope().bind_func(node.name, function_type.items())
        self.dup()
        for (v, t) in params:
            if v not in self.subst_var:
                self.bind_var(v, t)

        for stm in node.body:
            self.visit(stm)
        env = self.pop() 
        chans = env.get_kind(Node)
        for var, nd in chans:
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
        

    def visit_Compare(self, node: Compare) -> None:
        left = self.lookup_or_self(self.visit(node.left))
        right = self.lookup_or_self(self.visit(node.comparators[0]))
        res = union(left, right)
        return bool

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

            # More branches; no limits on 2
            #fail_if(not len(nd.outgoing) == 2, "Node should have 2 outgoing edges", SessionException)
            #fail_if(not len(node.cases) == 2, "Matching on session type operations should always have 2 cases", SessionException)
            offers = [key.key for key in nd.outgoing.keys()]
            for case in node.cases:
                match_value = case.pattern.value
                branch_pick = None
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
                            raise SessionException(f"Case '{branch_pick}' already visited")
                        offers.remove(branch_pick)
                        new_nd = nd.outgoing[edge]
                        break
                if new_nd == None:
                    raise SessionException(f"Case option '{ast.unparse(match_value)}' not an available offer")
                self.bind_var(ch_name, new_nd)
                for s in case.body:
                    self.visit(s)
                self.validate_postcondition()
            if offers:
                raise SessionException(f"Match cases were not exhaustive; paths not covered: {', '.join(offers)}")
            
        else:
            for case in node.cases:
                self.dup()
                case: ast.match_case = case
                p = self.visit(case.pattern)

                self.bind_var(p, self.lookup_or_self(subj))
                if case.guard:
                    self.visit(case.guard)

                for s in case.body:
                    self.visit(s)
                self.pop()

    def visit_MatchAs(self, node: ast.MatchAs) -> Union[str, None]:
        return node.name if node.name else None

    def visit_arguments(self, node: arguments) -> List[Tuple[str, type]]:
        arguments: ImmutableList[type] = ImmutableList()
        for arg in node.args:
            arguments = arguments.add(self.visit_arg(arg))
        return arguments.items()

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

    def visit_Tuple(self, node: Tuple) -> None:
        debug_print('visit_Tuple', dump(node))
        fail_if(not node.elts, "Tuple should contain elements", Exception)
        elems = []
        for el in node.elts: 
            # TODO: Hardcoding away forward-refs for now
            if isinstance(el, Name) and el.id.lower() in STR_ST_MAPPING:
                typ = STR_ST_MAPPING[el.id.lower()]
                elems.append(typ)
            else:
                elems.append(self.visit(el))
        return elems 

    def visit_List(self, node: List) -> None:
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
        if value == self: # TODO: Debug hack from within source
            invokable = getattr(self, attr)
            invokable()
            return
        if value in STR_ST_MAPPING or attr in STR_ST_MAPPING:
            return ChannelOperation(value, attr)
        else:
            assert False, ('value is', value, 'from ast', ast.unparse(node))
            env = self.get_latest_scope().lookup_nested(value)
            return env.lookup_func(attr)

    def visit_Assign(self, node: Assign) -> None:
        debug_print('visit_Assign', dump(node))
        fail_if(not len(node.targets) == 1, "Assigning multiple variables are not supported", Exception)

        target = self.visit(node.targets[0])

        if self.is_session_type(node.value):
            self.bind_session_type(node.value, target)
        else:
            value = self.visit(node.value)
            if isinstance(node.value, ast.Tuple):
                value = parameterise(Tuple, value)
            self.bind_var(target, value)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        debug_print('visit_AnnAssign', dump(node))
        target: str = self.visit(node.target)
        if self.is_session_type(node.value):
            self.bind_session_type(node.value, target)
        else:
            name_or_type = self.visit(node.annotation)
            rhs_type = self.visit(node.value)

            if isinstance(rhs_type, str):
                rhs_type = self.lookup_or_self(rhs_type)
            elif isinstance(name_or_type, typing._GenericAlias) and name_or_type.__origin__ == tuple:
                rhs_type = parameterise(Tuple, rhs_type)
            
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
        return union(l_typ, r_typ)

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
            for (param, typ), (arg_ast,arg) in zip(params, zip(node.args, visited_args)):
                if isinstance(typ, type) and isinstance(arg, type):
                    try:
                        union(typ, arg)
                    except TypeError:
                        raise IllegalArgumentException(f'function {func_name} got {param}={type_to_str(arg)} where it expected {param}={type_to_str(typ)}')
                if isinstance(arg, Node):
                    assert isinstance(param, str), "Expecting parameter to be a string"
                    assert isinstance(typ, SessionStub), "Expecting annotated type being a stub"
                    node_stub = STParser(src=typ.stub).build()
                    if arg != node_stub:
                        raise SessionException(f'function {func_name} received ill-typed session')
   
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
            out_edge = nd.get_edge()
            if isinstance(out_edge, Transition) and isinstance(out_edge.typ, str):
                aliased_typ = self.lookup_or_self(out_edge.typ)
                assert isinstance(aliased_typ, Typ)
                out_edge.typ = aliased_typ
            match op:
                case 'recv':
                    valid_action, _ = nd.valid_action_type(op, None)
                    if not valid_action:
                        raise SessionException(f'expected a {nd.outgoing_action()}, but recv was called')
                    next_nd = nd.next_nd()
                    self.bind_var(ch_name, next_nd)
                    return nd.outgoing_type()
                case 'send':
                    argument = args.head()

                    valid_action, valid_typ = nd.valid_action_type(op, argument)
                    if not valid_action:
                        raise SessionException(f'expected a {nd.outgoing_action()}, but send was called')
                    elif not valid_typ and argument != NoneType:
                        raise SessionException(f'expected to send a {type_to_str(nd.outgoing_type())}, got {type_to_str(argument)}')
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
                        assert isinstance(edge, BranchEdge)
                        if pick == edge.key:
                            new_nd = nd.outgoing[edge]
                            break
                    if not new_nd:
                        options = ', '.join(k.key for k in nd.outgoing.keys())
                        raise SessionException(f"The choice of '{pick}' is not one of: {options}")
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
            signature = ImmutableList.of_list(call_func)
            return_type = signature.last()
            call_func = signature.discard_last()
            func_name = node.func.attr if isinstance(node.func, Attribute) else node.func.id
            self.compare_function_arguments_and_parameters(func_name, provided_args, call_func)
            return return_type
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
        self.verify_loop(node)

    def visit_For(self, node: For) -> None:
        debug_print('visit_For', dump(node))
        target = self.visit(node.target)
        ite = self.visit(node.iter)
        assert isinstance(ite, ContainerType) or ite is str, ite
        typ = ite.__args__[0] if isinstance(ite, ContainerType) else str
        self.bind_var(target, typ)

        self.verify_loop(node)

    def visit_Dict(self, node: Dict) -> Dict[Typ, Typ]:
        debug_print('visit_Dict', dump(node))
        key_typ = reduce(union, ((self.visit(k)) for k in node.keys)) if node.keys else Any
        val_typ = reduce(union, ((self.visit(v)) for v in node.values)) if node.values else Any
        if isinstance(val_typ, list):
            val_typ = parameterise(Tuple, val_typ)
        res = Dict[key_typ, val_typ]
        return res

    def visit_Subscript(self, node: Subscript) -> Any:
        debug_print('visit_Subscript', dump(node))
        name = node.value.id.lower()
        if name in STR_ST_MAPPING:
            str_repr = self.process_and_substitute(node)
            if name == 'channel':
                return STParser(str_repr).build()
            return SessionStub(str_repr)
        else:
            name = self.lookup_or_self(name)
            if isinstance(name, str):
                container = str_to_typ(name)
                typs = self.visit(node.slice)
                if isinstance(typs, type | list):
                    return parameterise(to_typing(container), typs)
                else:
                    return to_typing(container)[typs]
            else:
                lookup_able = name
                assert isinstance(lookup_able, ContainerType)
                if lookup_able._name == 'Dict':
                    key_typ = self.visit(node.slice)
                    if key_typ == NoneType:
                        return Any
                    elif isinstance(key_typ, str):
                        key_typ = self.lookup_or_self(key_typ)
                    kv = lookup_able.__args__
                    if kv[0] == key_typ:
                        return kv[1]
                    else:
                        raise StaticTypeError(f'dictionary got key of type {type_to_str(key_typ)} where {type_to_str(kv[0])} was expected')


    def visit_Return(self, node: Return) -> Any:
        debug_print('visit_Return', dump(node))

        return_type = self.visit(node.value)

        return self.compare_type_to_latest_func_return_type(return_type)

    def visit_If(self, node: If) -> None:
        debug_print('visit_If', dump(node))

        self.visit(node.test)
        self.dup()
        for stm in node.body:
            self.visit(stm)
        env_if = self.pop()
        chans : list[(str,Node)] = env_if.get_kind(Node)

        if node.orelse:
            self.dup()
            for stm in node.orelse:
                self.visit(stm)
            env_else = self.pop()
            chans1 = env_else.get_kind(Node)
            for (ch1, nd1), (ch2, nd2) in zip(chans, chans1):
                # This is the scenario after and if-then-else block
                valid = nd1.accepting and nd2.accepting or nd1.identifier == nd2.identifier
                if ch1 == ch2 and not valid:
                    raise SessionException(f'after conditional block, channel <{ch1}> ended up in two different states')
        elif chans:
            latest = self.get_latest_scope()
            for (ch,nd) in chans:
                ch1 = latest.lookup_var(ch)
                if nd.identifier != ch1.identifier:
                    raise SessionException('then-block without else should not affect any session types')

        for (ch,nd) in chans:
            self.bind_var(ch, nd)


    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        return
        debug_print('visit_ImportFrom', dump(node))
        mod_name = f'{node.module}.py'
        if mod_name in sys.builtin_module_names:
            return
        ch_to_mod_dir(mod_name)
        typed_file = typechecker_from_path(mod_name)
        import_env = typed_file.get_latest_scope()
        to_import: Set[str] = {alias.name for alias in node.names}  # addition, zero

        for im in to_import:
            if import_env.contains_function(im):
                self.get_latest_scope().bind_func(im, import_env.lookup_func(im))
            elif import_env.contains_variable(im):
                self.bind_var(im, import_env.lookup_var(im))

    def visit_Import(self, node: Import) -> Any:
        return
        debug_print('visit_Import', dump(node))
        for module in node.names:
            module_name = module.name
            if module_name in sys.builtin_module_names:
                continue
            mod_name = f'{module_name}.py'
            ch_to_mod_dir(mod_name)
            typed_file = typechecker_from_path(mod_name)
            env = typed_file.get_latest_scope()
            self.get_latest_scope().bind_nested(module_name, env)

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

    def verify_loop(self, node: While | For):
        pre_chans = self.get_latest_scope().get_kind(Node)
        if pre_chans:
            nds = [chs[1] for chs in pre_chans]
            for nd in nds:
                self.loop_entrypoints.add(nd.identifier) 
            pre_chans = nds
        if isinstance(node, While):
            self.visit(node.test)
        for stm in node.body:
            self.visit(stm)
        post_chans = self.get_latest_scope().get_kind(Node)
        if pre_chans and post_chans:
            post_chans = [chs[1] for chs in post_chans]
            for post_chan in post_chans:
                if post_chan.identifier not in self.loop_entrypoints:
                    raise SessionException(f'loop error: needs to {post_chan.outgoing_action()()} {post_chan.outgoing_type()}')

    def process_and_substitute(self, node):
        alias_opts = self.get_latest_scope().get_kind(str)
        channel_str = ast.unparse(node) # 'Channel[Send[..., <Alias>]]'
        for key, val in alias_opts:
            channel_str = channel_str.replace(key, val)
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

    def is_session_type(self, node) -> bool:
        def check_subscript(node) -> bool:
            return isinstance(node, Subscript) and isinstance(node.value, Name) and node.value.id == 'Channel'
        return isinstance(node, Call) and check_subscript(node.func)

    def get_return_type(self, node: FunctionDef):
        return self.visit(node.returns) if node.returns else Any

    def get_function_args(self, args) -> ImmutableList:
        return ImmutableList.of_list([self.visit(arg) for arg in args])

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


def typechecker_from_path(file) -> TypeChecker:
    if file in visited_files:
        return visited_files[file]
    src = read_src_from_file(file)
    tree = parse(src)
    tc = TypeChecker(tree)
    visited_files[file] = tc
    return tc

def typecheck_file():
    return typechecker_from_path(sys.argv[0])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expected 1 argument, got 0')
        sys.exit()
    else:
        typechecker_from_path(sys.argv[1])


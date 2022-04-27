import ast
import copy
import sys
from ast import *
from functools import reduce

from debug import *
from environment import Environment
from immutable_list import ImmutableList
from lib import *
from statemachine import STParser, Node, TGoto
from sessiontype import STR_ST_MAPPING, SessionException

class TypeChecker(NodeVisitor):

    def __init__(self, tree, inside_class=False) -> None:
        self.inside_class = inside_class
        self.function_queue = {}
        self.functions_that_alter_channels = {}
        self.subst_var = {}
        self.channels = {}
        self.environments: ImmutableList[Environment] = ImmutableList().add(Environment())
        self.in_functions: ImmutableList[FunctionDef] = ImmutableList()
        self.loop_entrypoints = set() # TODO: consider putting into environment
        self.visit(tree)
        self.visit_functions()
        self.validate_postcondition()
        print('Typechecking done, found the channels =', self.channels)

    def visit_and_drop_function(self, key: str) -> None:
        env = self.get_latest_scope()
        #assert key in self.function_queue and not env.contains_function(key), "You may only call this function if you know we haven't evaluated it yet"
        function = self.function_queue[key] if key in self.function_queue else self.functions_that_alter_channels[key]
        self.visit(function)
        if key in self.function_queue:
            del self.function_queue[key]


    def visit_functions(self):
        """
        For testing to work we would have to exhaust the dictionary of functions
        before checking post-conditions.
        Due to nested function, we need to do it inside a loop.
        """
        while self.function_queue:
            for name in list(self.function_queue.keys()):
                self.visit_and_drop_function(name)
        


    def validate_postcondition(self):
        latest = self.get_latest_scope()
        failing_chans = []
        for (k,v) in latest.get_vars():
            if isinstance(v, Node):
                if not v.accepting and v.id not in self.loop_entrypoints:
                    err_msg = f'\nchannel <{k}> not exhausted - next up is:'
                    for edge in v.outgoing.keys():
                        err_msg += f'\n- {str(edge)}'
                    failing_chans.append(err_msg)
        if failing_chans:
            msgs = '\n'.join(failing_chans)
            raise SessionException(msgs)

    def visit_FunctionDef(self, node: FunctionDef) -> Typ:
        in_queue = self.in_function_queue(node.name)
        if not in_queue and not self.inside_class:
            self.function_queue[node.name] = node
        if not in_queue and node.name not in self.functions_that_alter_channels and not self.inside_class:
            return
        self.in_functions = self.in_functions.add(node)
        expected_return_type: type = self.get_return_type(node)
        params = self.visit(node.args)
        if self.inside_class:
            fail_if(params[0][0] != 'self', "a class function must have self as first parameter")
            params = params[1:]
        function_type: ImmutableList[Tuple[str, type]] = \
            ImmutableList.of_list(params).map(lambda tp: tp[1]).add(expected_return_type)

        self.get_latest_scope().bind_func(node.name, function_type.items())
        self.dup()
        chans = self.get_latest_scope().get_kind(Node)
        if chans:
            for v, t in params:
                for ch, nd in chans:
                    if not isinstance(nd, Node) and not v in self.subst_var and v != ch:
                        self.bind_var(v, t)
        else:
            for (v, t) in params:
                if not v in self.subst_var:
                    self.bind_var(v, t)

        for stm in node.body:
            self.visit(stm)


        # Popping, but if we updated any channels in a lower scope, we need to
        # bring them up to speed
        env = self.pop()
        chans = env.get_kind(Node)
        for name, ch in chans:
            current_env = self.get_latest_scope()
            if current_env.contains_variable(name):
                self.functions_that_alter_channels[node.name] = node
                self.bind_var(name, ch)

        
        self.in_functions = self.in_functions.tail()

        return function_type.items()

    def visit_Compare(self, node: Compare) -> None:
        left = self.lookup_or_self(self.visit(node.left))
        right = self.lookup_or_self(self.visit(node.comparators[0]))
        fail_if_cannot_cast(left, right, f"{left} did not equal {right}")
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

            fail_if(not len(nd.outgoing) == 2, "Node should have 2 outgoing edges", SessionException)
            fail_if(not len(node.cases) == 2, "Matching on session type operations should always have 2 cases", SessionException)
            
            for case in node.cases:
                match_value = case.pattern
                attribute = match_value.value
                branch_pick = attribute.attr
                fail_if(not attribute.value.id == 'Branch', "Match case did not contain a Branch", SessionException)
                fail_if(not branch_pick in ['LEFT', 'RIGHT'], "Branching operation should either be left or right", SessionException)

                self.bind_var(ch_name, nd)
                new_nd = nd.outgoing[Branch.LEFT if branch_pick == 'LEFT' else Branch.RIGHT]
                self.bind_var(ch_name, new_nd)
                for s in case.body:
                    self.visit(s)
                self.validate_postcondition()
            
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
        if name in self.functions_that_alter_channels:
            return name
        print('name', name)
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
        if value == self: # TODO: Debug hack from within source
            invokable = getattr(self, attr)
            invokable()
            return
        if value in STR_ST_MAPPING or attr in STR_ST_MAPPING:
            return value, attr
        else:
            env = self.get_latest_scope().lookup_nested(value)
            return env.lookup_func(attr)

    def visit_Assign(self, node: Assign) -> None:
        debug_print('visit_Assign', dump(node))
        fail_if(not len(node.targets) == 1, "Assigning multiple variables are not supported", Exception)

        target = self.visit(node.targets[0])

        if self.is_session_type(node.value):
            self.bind_session_type(node, target)
        else:
            value = self.visit(node.value)
            if isinstance(node.value, ast.Tuple):
                value = parameterise(Tuple, value)
            self.bind_var(target, value)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        debug_print('visit_AnnAssign', dump(node))
        target: str = self.visit(node.target)
        if self.is_session_type(node.value):
            self.bind_session_type(node, target)
        else:
            name_or_type = self.visit(node.annotation)
            rhs_type = self.visit(node.value)
            if isinstance(name_or_type, typing._GenericAlias) and name_or_type.__origin__ == tuple:
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

    def visit_Call(self, node: Call) -> Typ:
        debug_print('visit_Call', dump(node))
        call_func = self.visit(node.func)
        if isinstance(call_func, str) and call_func == 'Channel':
            for arg in node.args:
                print('arg=', arg)
                v = self.visit(arg)
                if isinstance(arg, Subscript):
                    parsed = STParser(src=v)
                    return parsed.build()
        elif isinstance(call_func, str) and (call_func in self.function_queue or call_func in self.functions_that_alter_channels):
            visited_args = [self.visit(arg) for arg in node.args]
            function: FunctionDef = self.function_queue[call_func] if call_func in self.function_queue else self.functions_that_alter_channels[call_func]
            if any(isinstance(arg, Node) for arg in visited_args):
                # We passed a channel to a function
                params = self.visit(function.args)
                pre_subst = copy.deepcopy(self.subst_var)
                self.functions_that_alter_channels[call_func] = function
                for (param, typ), (arg_ast,arg) in zip(params, zip(node.args, visited_args)):
                    if isinstance(arg, Node):
                        if isinstance(arg_ast, Name):
                            self.subst_var[param] = arg_ast.id
                        else:
                            unioned = union(typ, arg)
                            self.channels[param] = unioned
                            self.bind_var(param, unioned)
                    
                
                self.visit_and_drop_function(call_func)
                call_func = self.visit(node.func)
                self.subst_var = pre_subst

            else:
                self.visit_and_drop_function(call_func)
                call_func = self.visit(node.func)
        
        if isinstance(call_func, tuple):
            args = self.get_function_args(node.args)
            op = call_func[1]
            ch_name = node.func.value.id
            nd = self.get_latest_scope().try_find(ch_name)
            if not nd or nd and not isinstance(nd, Node):
                nd = call_func[0]
            if ch_name in self.subst_var:
                ch_name = self.subst_var[ch_name]
            match op:
                case 'recv':
                    valid_action, _ = nd.valid_action_type(op, None)
                    if not valid_action:
                        raise SessionException(f'expected a {nd.outgoing_action()}, but recv was called')
                    next_nd = nd.next_nd()
                    self.bind_var(ch_name, next_nd)
                    return nd.outgoing_type()
                case 'send':
                    if isinstance(args.head(), list): # TODO(Johan): Feels hacky; Tuple always returns lists now, but this only *sometimes* have to get parameterised. How to solve?
                        items = args.items()
                        items[0] = parameterise(Tuple, items[0])
                        args = ImmutableList.of_list(items)
                    valid_action, valid_typ = nd.valid_action_type(op, args.head())

                    if not valid_action:
                        raise SessionException(f'expected a {nd.outgoing_action()}, but send was called')
                    elif not valid_typ:
                        raise SessionException(f'expected to send a {type_to_str(nd.outgoing_type())}, got {type_to_str(args.head())}')
                    next_nd = nd.next_nd()
                    self.bind_var(ch_name, next_nd)
                case 'offer':
                    return nd
                case 'choose':
                    new_nd = nd.outgoing[Branch.LEFT if args.head()[1] == 'LEFT' else Branch.RIGHT]
                    fail_if(new_nd is None, "Choose outgoing node was none", SessionException)
                    # FIXME: sanitise goto-skips
                    if new_nd.outgoing and isinstance(new_nd.get_edge(), TGoto):
                        new_nd = new_nd.next_nd()
                    self.bind_var(ch_name, new_nd)
                    return nd
                    
        elif isinstance(call_func, FunctionTyp):
            signature = ImmutableList.of_list(call_func)
            return_type = signature.last()
            call_func = signature.discard_last()

            provided_args = self.get_function_args(node.args)

            func_name = node.func.attr if isinstance(node.func, Attribute) else node.func.id

            self.compare_function_arguments_and_parameters(func_name, provided_args, call_func)
            return return_type
        return call_func

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
        res = Dict[key_typ, val_typ]
        return res

    def visit_Subscript(self, node: Subscript) -> Any:
        debug_print('visit_Subscript', dump(node))
        name = node.value.id.lower()
        if name in STR_ST_MAPPING:
            if name == 'channel':
                return STParser(ast.unparse(node)).build()
            #fail_if(name == 'channel', "Subscript cannot contain a channel", SessionException)
            return ast.unparse(node)
        else:
            container = str_to_typ(name)
            typs = self.visit(node.slice)
            if isinstance(typs, type | list):
                return parameterise(to_typing(container), typs)
            else:
                return to_typing(container)[typs]

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
                valid = nd1.accepting and nd2.accepting or nd1.id == nd2.id
                if ch1 == ch2 and not valid:
                    raise SessionException(f'after conditional block, channel <{ch1}> ended up in two different states')
        elif chans:
            latest = self.get_latest_scope()
            for (ch,nd) in chans:
                ch1 = latest.lookup_var(ch)
                if nd.id != ch1.id:
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
            can_upcast: bool = can_upcast_to(actual_type, expected_type)
            fail_if(types_differ and not can_upcast,
                    f'function <{func_name}> expected {parameters}, got {arguments}')

    def verify_loop(self, node: While | For):
        pre_chans = self.get_latest_scope().get_kind(Node)
        if pre_chans:
            nds = [chs[1] for chs in pre_chans]
            for nd in nds:
                self.loop_entrypoints.add(nd.id) 
            pre_chans = nds
        if isinstance(node, While):
            self.visit(node.test)
        for stm in node.body:
            self.visit(stm)
        post_chans = self.get_latest_scope().get_kind(Node)
        if pre_chans and post_chans:
            post_chans = [chs[1] for chs in post_chans]
            for post_chan in post_chans:
                if post_chan.id not in self.loop_entrypoints:
                    raise SessionException(f'loop error: needs to {post_chan.outgoing_action()()} {post_chan.outgoing_type()}')

    def bind_session_type(self, node, target):
            alias_opts = self.get_latest_scope().get_kind(str)
            channel_str = ast.unparse(node.value) # 'Channel[Send[..., <Alias>]]'
            for key, val in alias_opts:
                fail_if(not key in channel_str, f"{key} was not found in {channel_str}", SessionException)
                channel_str = channel_str.replace(key, val)
            nd = STParser(src=channel_str).build()
            self.channels[target] = nd
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
        self.get_latest_scope().bind_var(var, typ)

    def print_envs(self, opt_title='') -> None:
        i = 0
        for env in self.environments.items():
            print(f'Env #{i}:', env)
            i += 1


def typechecker_from_path(file) -> TypeChecker:
    src = read_src_from_file(file)
    print('got the src', src)
    tree = parse(src)
    tc = TypeChecker(tree)
    return tc

def typecheck_file():
    return typechecker_from_path(sys.argv[0])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expected 1 argument, got 0')
        sys.exit()
    else:
        typechecker_from_path(sys.argv[1])


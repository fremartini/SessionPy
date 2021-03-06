from __future__ import annotations

from ast import *
from types import EllipsisType, GenericAlias
from typing import ForwardRef, Any, Iterable, Tuple
import typing
from debug import dump_object
import sessiontype

from lib import Typ, parameterise, str_to_typ, to_typing, type_to_str, SessionException, union
from sessiontype import *

A = TypeVar('A')


class Action(str, Enum):
    """
    Action is an enumeration of what a transition can be.
    """
    SEND = 'send'
    RECV = 'recv'
    LABEL = 'label'
    BRANCH = 'branch'


class BranchEdge:
    """
    BranchEdge is a specialised transition for choice/offers.
    """
    def __init__(self, key: str, actor: str) -> None:
        self.key = key
        self.actor = actor

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, type(self)) and \
               self.key == __o.key

    def __hash__(self) -> int:
        return hash(self.key + self.actor)

    def __str__(self) -> str:
        return f"'{self.key}' @ {self.actor}"

    def __repr__(self) -> str:
        return self.__str__()


class Transition:
    """
    Transition in the state machine; depending on action encapsulates different arguments.
    """
    def __init__(self, action: Action) -> None:
        self.action: Action = action
        self.actor: str | None = None
        if action in [Action.SEND, Action.RECV]:
            self.typ = Any
        elif action == Action.BRANCH:
            self.branch_options = {}
        elif action == Action.LABEL:
            self.name = ''
            self.st = None

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, type(self)):
            return False
        if self.action in [Action.SEND, Action.RECV]:
            try: 
                union(self.typ, __o.typ)
            except:
                return False
            return self.actor == __o.actor
        elif self.action == Action.BRANCH:
            return self.action == __o.action and self.actor == __o.actor and self.left == __o.left and self.right == __o.right
        elif self.action == Action.LABEL:
            return self.name == __o.name and self.st == __o.st
        return False

    def __hash__(self) -> int:
        if self.action in [Action.SEND, Action.RECV]:
            return hash(self.action) + hash(self.typ) + hash(self.actor)
        elif self.action in [Action.LEFT, Action.RIGHT]:
            return hash(self.action) + hash(self.actor)
        elif self.action == Action.LABEL:
            return hash(self.name) + hash(self.st)

    def __repr__(self) -> str:
        res = ''
        if self.action in [Action.SEND, Action.RECV]:
            res += f'{self.action.value} {type_to_str(self.typ)}'
        elif self.action == Action.BRANCH:
            res += f'{self.action}({self.branch_options})'
        elif self.action == Action.LABEL:
            res += f'{self.name} => {self.st}'
        if self.actor:
            return res + f" @ {self.actor}"
        return res



class STEnd:
    def __str__(self) -> str:
        return 'end'

    def __repr__(self) -> str:
        return self.__str__()


class TGoto:
    def __init__(self, lab) -> None:
        self.lab = lab

    def get_label(self):
        return self.lab

    def __repr__(self) -> str:
        return f'goto {self.lab}'


class State:
    """
    State in the state machine that encapsulates id, bool if it's accepting or not, and outgoing edges.
    """
    def __init__(self, identifier: int, accepting_state: bool = False) -> None:
        self.identifier = identifier
        self.accepting = accepting_state
        self.any_state = False
        self.outgoing = {}

    def __str__(self) -> str:
        state = f'(s{self.identifier})' if self.accepting else f's{self.identifier}'
        state += '...' if self.any_state else ''
        return f'SessionType(state={state})'

    def __repr__(self) -> str:
        return f'State(state={self.identifier})'

    def __eq__(self, current_state: State) -> bool:
        if not isinstance(current_state, State):
            return False
        if self.any_state or current_state.any_state:
            return True
        if len(self.outgoing) == 0 or len(current_state.outgoing) == 0:
            return self.accepting == current_state.accepting

        if len(self.outgoing) == 1 and len(current_state.outgoing) == 1:
            e1 = self.get_edge()
            e2 = current_state.get_edge()
            return e1 == e2 and self.next_nd() == current_state.next_nd()
        else:
            res = False
            for k1, k2 in zip(self.outgoing, current_state.outgoing):
                res = k1 == k2 and self.outgoing[k1] == current_state.outgoing[k2]
                if not res:
                    return res
            return res

    def next_nd(self) -> State:
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        points_to = list(self.outgoing.values())[0]
        if points_to.outgoing and isinstance(points_to.get_edge(), TGoto):
            points_to = points_to.next_nd()
            assert not isinstance(points_to.get_edge(), TGoto), "Wow now, are you trying to break something?"
        return points_to

    def get_edge(self) -> Transition:
        assert len(self.outgoing) > 0, "Function should at least contain a single edge"
        return list(self.outgoing.keys())[0]

    def outgoing_actor(self) -> str:
        if len(self.outgoing) == 0:
            raise SessionException(f'Endpoint {self} is exhausted')
        edge = self.get_edge()
        return edge.actor

    def outgoing_action(self) -> Action | Transition:
        if len(self.outgoing) == 0:
            raise SessionException(f'Endpoint {self} is exhausted')
        edge = self.get_edge()
        if isinstance(edge, BranchEdge):
            return Action.BRANCH
        else:
            assert isinstance(edge, Transition), edge
            return edge.action

    def outgoing_type(self) -> type | None:
        key = self.get_edge()
        if isinstance(key, BranchEdge):
            return None
        typ = key.typ
        assert isinstance(typ, Typ), typ
        return typ

    def valid_action_type(self, action: str, typ: None | type = Any) -> tuple[bool, bool]:
        str_transition_map = {
            "recv": Transition(Action.RECV),
            "send": Transition(Action.SEND),
            "offer": Transition(Action.BRANCH),
            "choice": Transition(Action.BRANCH),
        }

        assert action in str_transition_map, action
        return action == self.outgoing_action(), typ == self.outgoing_type() or typ is Any


def from_generic_alias(typ: GenericAlias) -> State:
    stp = STParser(typ=typ)
    return stp.build()


class STParser(NodeVisitor):
    """
    Parses a sessiontype and stores it in a tuple (self.res):
        parsed = STParser("Endpoint[Recv[str, Offer[Send[bool, End], Loop[Send[int, End]]]]]")
        parsed.res # (recv, (<class 'str'>, (offer, ((send, (<class 'bool'>, end)), (loop, (send, (<class 'int'>, end)))))))
    """

    def __init__(self, src: str = '', typ: GenericAlias = None) -> None:
        self.session_tuple = None
        self.identifier = 0
        if src:
            tree = parse(src)
            self.root = self.new_node()
            self.visit(tree)
        else:
            self.session_tuple = self.from_generic_alias(typ)

        assert self.session_tuple, (src, typ)

    def get_transition(self, key) -> Transition | STEnd:
        match key:
            case sessiontype.Send:
                return Transition(Action.SEND)
            case sessiontype.Recv:
                return Transition(Action.RECV)
            case sessiontype.Offer:
                return Transition(Action.BRANCH)
            case sessiontype.Choose:
                return Transition(Action.BRANCH)
            case sessiontype.Label:
                return Transition(Action.LABEL)
            case sessiontype.End:
                return STEnd()

    def process_generic_alias(self, typ):
        if isinstance(typ, GenericAlias):
            # A parameterised type like dict[str, int], list[bool], etc.
            container = to_typing(typ.__origin__)
            return parameterise(container, typ.__args__)
        return typ

    def from_generic_alias(self, typ: GenericAlias):
        if typ == End:
            return STEnd()
        if isinstance(typ, ForwardRef):
            return typ.__forward_arg__
        if isinstance(typ, EllipsisType):
            return typ
        base = self.get_transition(typ.__origin__)
        assert isinstance(base, Transition), base
        if base.action in [Action.SEND, Action.RECV]:
            base.typ = typ.__args__[0]
            base.typ = self.process_generic_alias(base.typ)
            base.actor = typ.__args__[1].__forward_arg__
            return base, self.from_generic_alias(typ.__args__[2])
        elif base.action == Action.BRANCH:
            base.actor = typ.__args__[0].__forward_arg__
            for branch_key in typ.__args__[1]:
                value = typ.__args__[1][branch_key]
                edge = BranchEdge(branch_key, base.actor)
                base.branch_options[edge] = self.from_generic_alias(value)
            return base
        elif base.action == Action.LABEL:
            base.name = typ.__args__[0].__forward_arg__
            base.st = self.from_generic_alias(typ.__args__[1])
            return base

    def next_id(self) -> int:
        res = self.identifier
        self.identifier += 1
        return res

    def new_node(self) -> State:
        return State(self.next_id())

    def visit_Name(self, node: Name) -> Any:
        match node.id:
            case sessiontype.Send | 'Send':
                return Transition(Action.SEND)
            case sessiontype.Recv | 'Recv':
                return Transition(Action.RECV)
            case sessiontype.End | 'End':
                return STEnd()
            case sessiontype.Offer | 'Offer':
                return Transition(Action.BRANCH)
            case sessiontype.Choose | 'Choose':
                return Transition(Action.BRANCH)
            case sessiontype.Label | 'Label':
                return Transition(Action.LABEL)
            case 'Endpoint':
                return None
            case EllipsisType():
                return EllipsisType()
            case x:
                res = str_to_typ(x) or x
                return res

    def visit_Tuple(self, node: Tuple) -> tuple[Any]:
        elements = [self.visit(el) for el in node.elts]
        return tuple(elements)

    def visit_Dict(self, node: Dict) -> Any:
        keys_vals = zip([self.visit(k) for k in node.keys], [self.visit(v) for v in node.values])
        return keys_vals

    def visit_Subscript(self, node: Subscript) -> tuple[Any, Any] | None:
        value = self.visit(node.value)
        slice = self.visit(node.slice)
        if isinstance(slice, EllipsisType):
            return value, slice
        if isinstance(value, Transition):
            if value.action in [Action.SEND, Action.RECV]:
                value.typ = slice[0]
                if len(slice) == 3:
                    value.actor = slice[1]
                    slice = slice[2:][0]
                else:
                    slice = slice[1:][0]
            elif value.action == Action.BRANCH:
                actor, keyvals = slice
                value.actor = slice[0]
                if isinstance(keyvals, Iterable):
                    for key, val in keyvals:
                        edge = BranchEdge(key, actor)
                        value.branch_options[edge] = val
                slice = slice[1:]
            elif value.action == Action.LABEL:
                value.name = slice[0]
                value.st = slice[1]
                slice = slice[1:][0]

        if not value:
            self.session_tuple = slice
            return
        self.session_tuple = slice if not value else (value, slice)
        return value, slice

    def visit_Constant(self, node: Constant) -> Any:
        assert isinstance(node.value, str | EllipsisType)
        return self.visit(Name(node.value))

    def build(self) -> State:
        global ident
        ident = 0

        def next_id():
            global ident
            res = ident
            ident += 1
            return res

        def new_node() -> State:
            return State(next_id())

        root = new_node()
        ref = root

        labels = {}
        forwarded_labs = {}

        def go(tup, node: State):
            if isinstance(tup, STEnd):
                node.accepting = True
                return node, None
            elif isinstance(tup, EllipsisType):
                node.any_state = True
                return tup
            elif isinstance(tup, str):
                lab = tup
                if lab in labels:
                    goto_trans = TGoto(lab)
                    node.outgoing[goto_trans] = labels[lab]
                else:
                    forwarded_labs[lab] = node
            if isinstance(tup, Transition):
                head = tup
            else:
                head, tail = tup[0], tup[1]
            if isinstance(head, Transition):
                if head.action == Action.LABEL:
                    lab = head.name
                    tl = head.st
                    labels[lab] = node
                    if lab in forwarded_labs:
                        forwarded_labs[lab].outgoing[TGoto(lab)] = node
                    if isinstance(tl, str):
                        assert tl in labels, tl
                        goto_trans = TGoto(tl)
                        node.outgoing[goto_trans] = labels[tl]
                    else:
                        go(tl, node)
                elif head.action in [Action.SEND, Action.RECV]:
                    current_state = new_node()
                    if isinstance(head.typ, tuple):
                        head.typ = parameterise(to_typing(head.typ[0]), [head.typ[1]])
                    go(tail, current_state)
                    node.outgoing[head] = current_state
                    return current_state, head
                elif head.action == Action.BRANCH:
                    options = head.branch_options
                    for branch_key in options:
                        branch_nd = new_node()
                        branch_st = options[branch_key]
                        go(branch_st, branch_nd)
                        node.outgoing[branch_key] = branch_nd
                    return list(node.outgoing.values())
            head = head.__class__
            if head == STEnd:
                node.accepting = True

        go(self.session_tuple, ref)
        return root


def print_node(n: State) -> None:
    if not n.outgoing:
        return
    print(n)
    seen = set()
    for key in n.outgoing:
        if key in seen:
            return
        s = ''
        if isinstance(key, BranchEdge):
            s += f'{key} -> {n.outgoing[key]}'
        elif isinstance(key, typing._GenericAlias):
            typ = key.__args__[0]
            s += f'{key()} {typ} -> {n.outgoing[key]}'
        elif isinstance(key, Transition):
            s += f'{str(key)} -> {n.outgoing[key]}'
        else:
            assert isinstance(key, TGoto | BranchEdge), (key, type(key))
            seen.add(key.get_label())
            s += f'goto {n.outgoing[key]}'
        print(s)

    for key in n.outgoing:
        print()
        key = key.get_label() if isinstance(key, TGoto) else key
        if key in seen:
            return
        seen.add(key)
        n1 = n.outgoing[key]
        if n1.identifier != n.identifier:
            print_node(n1)

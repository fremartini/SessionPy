from ast import *
from enum import Enum
from typing import TypeVar, Generic, Any
import typing

from lib import Typ, parameterise, str_to_typ, to_typing
from sessiontype import SessionException

A = TypeVar('A')

class Action(str, Enum):
    SEND = 'send'
    RECV = 'recv'
    BRANCH = 'branch'

class Direction(str, Enum):
    LEFT = 'left'
    RIGHT = 'right'
    

class Transition():
    def __init__(self, action : Action, typ=Any, actor=Any) -> None:
        self.typ = typ
        self.action = action
        self.actor = actor
        if self.action == Action.BRANCH:
            self.left = None
            self.right = None

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        if self.action == Action.BRANCH:
            str_repr = f'Branch(Left: {self.left}, Right: {self.right})'
            return f'{str_repr} @ {self.actor}' if self.actor else str_repr
        str_repr = f'{self.action} {self.typ}'
        if self.actor:
            str_repr += f' @ {self.actor}'
        return str_repr

    def __eq__(self, other: object) -> bool:
        return self.typ == other.typ and self.action == other.action and self.actor == other.actor
    
    def __hash__(self) -> int:
        key = self.__str__()
        return hash(key)



class TLabel(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'label'

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


str_transition_map = {
    "recv": Transition(Action.RECV),
    "send": Transition(Action.SEND),
    "offer": Transition(Action.BRANCH),
    "choice": Transition(Action.BRANCH),
}


class Node:
    def __init__(self, id: int, accepting_state: bool = False) -> None:
        self.id = id
        self.accepting = accepting_state
        self.outgoing: dict[Transition, Node] = {}

    def __str__(self) -> str:
        state = f'(s{self.id})' if self.accepting else f's{self.id}'
        return state

    def __repr__(self) -> str:
        return f'Node(state={self.id})'

    def next_nd(self):
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        points_to = list(self.outgoing.values())[0]
        if points_to.outgoing and isinstance(points_to.get_edge(), TGoto):
            points_to = points_to.next_nd()
            assert not isinstance(points_to.get_edge(), TGoto), "Wow now, are you trying to break something?"
        return points_to

    def get_edge(self):
        assert len(self.outgoing) > 0, "Function should at least contain a single edge"
        return list(self.outgoing.keys())[0]

    def outgoing_action(self):
        if len(self.outgoing) == 0:
            raise SessionException(f'Channel {self} is done and exhausted')
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        key = self.get_edge()
        return key.action

    def outgoing_type(self) -> type:
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        key = self.get_edge()
        typ = key.typ
        assert isinstance(typ, Typ)
        return typ

    def valid_action_type(self, action: str, typ: type = Any):
        assert action in str_transition_map, action
        print('action_str', action)
        print('outgoing_action', self.outgoing_action())
        print('typ', typ)
        print('outgoing typ', self.outgoing_type())
        return action == self.outgoing_action(), typ == self.outgoing_type() or typ is Any


class STParser(NodeVisitor):
    """
    Parses a sessiontype and stores it in a tuple (self.res):
        parsed = STParser("Channel[Recv[str, Offer[Send[bool, End], Loop[Send[int, End]]]]]")
        parsed.res # (recv, (<class 'str'>, (offer, ((send, (<class 'bool'>, end)), (loop, (send, (<class 'int'>, end)))))))
    """

    def __init__(self, src: str):
        print(src)
        self.session_tuple = None
        self.id = 0
        tree = parse(src)
        self.root = self.new_node()
        self.visit(tree)
        assert self.session_tuple

    def next_id(self) -> int:
        res = self.id
        self.id += 1
        return res

    def new_node(self) -> Node:
        return Node(self.next_id())

    def visit_Name(self, node: Name) -> Any:
        match node.id.lower():
            case 'send':
                return Transition(Action.SEND, actor=None)
            case 'send1':
                return Transition(Action.SEND)
            case 'recv':
                return Transition(Action.RECV, actor=None)
            case 'recv1':
                return Transition(Action.RECV)
            case 'end':
                return STEnd()
            case 'offer':
                return Transition(Action.BRANCH, actor=None)
            case 'choice':
                return Transition(Action.BRANCH, actor=None)
            case 'choice1':
                return Transition(Action.BRANCH)
            case 'label':
                return TLabel()
            case 'channel':
                return None
            case x:
                res = str_to_typ(x) or x
                return res

    def visit_Tuple(self, node: Tuple) -> Any:
        elems = [self.visit(el) for el in node.elts]
        return tuple(elems)

    def visit_Subscript(self, node: Subscript) -> Any:
        value = self.visit(node.value)
        slice = self.visit(node.slice)
        print('\nvalue', value)
        print('slice', slice)
        if not value:
            self.session_tuple = slice
            return

        if isinstance(value, Transition):
            if value.actor:
                if value.action == Action.BRANCH:
                    actor = slice[0]
                else:
                    actor = slice[1]
                assert type(actor) is str, actor
                value.actor = actor
            if value.action == Action.BRANCH:
                offset = 0
                if value.actor:
                    offset = 1
                value.left = slice[0 + offset]
                value.right = slice[1 + offset]
                return value
            else:
                typ = slice[0]
                #assert type(typ) is type, typ
                value.typ = typ
            if value.actor or value.action == Action.BRANCH:
                slice = slice[2:]
            else:
                slice = slice[1:]
        print('slice is', slice)
        if type(slice) == list:
            slice = slice[0]
        print('new value', value)
        print('new slice', slice)
        self.session_tuple = slice if not value else (value, slice)
        return value, slice

    def visit_Constant(self, node: Constant) -> Any:
        assert isinstance(node.value, str)
        return self.visit(Name(node.value))

    def build(self):
        global ident
        ident = 0

        def next_id():
            global ident
            res = ident
            ident += 1
            return res

        def new_node() -> Node:
            return Node(next_id())

        root = new_node()
        ref = root

        labels = {}
        forwarded_labs = {}

        def go(tup, node: Node):
            if isinstance(tup, STEnd):
                node.accepting = True
                return node, None
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

            if head.action in [Action.SEND, Action.RECV]:
                nd = new_node()
                go(tail,nd)
                node.outgoing[head] = nd
                return nd, head
            elif head.action == Action.BRANCH:
                print('we found a branch')
                st1, st2 = head.left, head.right
                l, r = new_node(), new_node()
                go(st1, l)
                go(st2, r)
                node.outgoing[Direction.LEFT] = l
                node.outgoing[Direction.RIGHT] = r
                return l, r
            else: 
                head = head.__class__
            if head in [TOffer, TChoose]:
                st1, st2 = tail[0], tail[1]
                l, r = new_node(), new_node()
                go(st1, l)
                go(st2, r)
                tl, tr = TLeft, TRight
                node.outgoing[tl] = l
                node.outgoing[tr] = r
                return l, r
            elif head in [TLabel]:
                lab = tail[0]
                tl = tail[1]
                labels[lab] = node
                if lab in forwarded_labs:
                    forwarded_labs[lab].outgoing[TGoto(lab)] = node
                if isinstance(tl, str):
                    assert tl in labels, tl
                    goto_trans = TGoto(tl)
                    node.outgoing[goto_trans] = labels[tl]
                else:
                    _, key = go(tl, node)
            else:
                if head == STEnd:
                    node.accepting = True

        go(self.session_tuple, ref)
        return root


def print_node(n: Node):
    if not n.outgoing:
        return
    print(n)
    seen = set()
    for key in n.outgoing:
        if key in seen:
            return
        s = ''
        if isinstance(key, Transition):
            if key.action in [Action.SEND, Action.RECV]:
                typ = key.typ
                s += f'{key} -> {n.outgoing[key]}'
            else:
                s += f'left  -> {key.left}'
                s += f'right -> {key.right}'
        elif isinstance(key, typing._GenericAlias):
            typ = key.__args__[0]
            s += f'{key()} {typ} -> {n.outgoing[key]}'
        elif isinstance(key, Direction):
            s += f'{key} -> {n.outgoing[key]}'
        else:
            assert isinstance(key, TGoto), key
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
        if n1.id != n.id:
            print_node(n1)


if __name__ == '__main__':
    #st = STParser("Channel[Send[int, Recv[str, End]]]")
    st1 = OldSTParser("Channel[Send[List[int], Send[Tuple[str, int], Send[Dict[int, float], End]]]]")
    #st_actor = STParser("Channel[Send1[int, 'Alice', Recv1[str, 'Bob', End]]]")
    print('tuple:', st1.session_tuple)
    nd = st1.build()
    print_node(nd)
    # print('no actor:', st.session_tuple)
    # print('w/ actor:', st_actor.session_tuple)

    # print('no actor:')
    # print_node(st.build())
    # print('w/ actor:')
    # print_node(st_actor.build())
    # nd = st.build()
    # print_node(nd)

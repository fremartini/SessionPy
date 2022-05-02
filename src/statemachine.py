from ast import *
from enum import Enum
from types import GenericAlias
from typing import ForwardRef, TypeVar, Generic, Any
import typing
import sessiontype

from lib import ContainerType, Typ, parameterise, str_to_typ, to_typing, Branch, type_to_str
from sessiontype import *

A = TypeVar('A')

class Action(str, Enum):
    SEND = 'send'
    RECV = 'recv'
    LABEL = 'label'
    BRANCH = 'branch'


"""
Send TYPE [@ Actor]
Receive TYPE [@ Actor]
Label NAME SESSIONTYPE [@ Actor]
Offer   ST_LEFT ST_RIGHT [@ Actor]
Choice  ST_LEFT ST_RIGHT [@ Actor]
"""


class Transition:

    def __init__(self, action) -> None:
        self.action = action
        self.actor = None
        if action in [Action.SEND, Action.RECV]:
            self.typ = Any
        elif action == Action.BRANCH:
            self.left = None
            self.right = None
        elif action == Action.LABEL:
            self.name = ''
            self.st = None
        
    def __eq__(self, __o: object) -> bool:
        if self.action in [Action.SEND, Action.RECV]:
            return self.typ == __o.typ and self.actor == __o.actor
        elif self.action == Action.BRANCH:
            return self.left == __o.left and self.right == __o.right
        elif self.action == Action.LABEL:
            return self.name == __o.name and self.st == __o.st
        return False


    def __hash__(self) -> int:
        if self.action in [Action.SEND, Action.RECV]:
            return hash(self.action) + hash(self.typ) + hash(self.actor)
        elif self.action == Action.BRANCH:
            return hash(self.action) + hash(self.left) + hash(self.right)
        elif self.action == Action.LABEL:
            return hash(self.name) + hash(self.st)

    def __repr__(self) -> str:
        res = ''
        if self.action in [Action.SEND, Action.RECV]:
            res += f'{self.action.value} {type_to_str(self.typ)}'
        elif self.action == Action.BRANCH:
            res += f'{self.action}(left: {self.left}, right: {self.right})'
        elif self.action == Action.LABEL:
            res += f'{self.name} => {self.st}'
        if self.actor:
            return res + f" @ {self.actor}"
        return res
    
        

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

    def get_edge(self, opt_branch=None):
        assert len(self.outgoing) > 0, "Function should at least contain a single edge"
        return list(self.outgoing.keys())[0]

    def outgoing_action(self):
        if len(self.outgoing) == 0:
            raise SessionException(f'Channel {self} is done and exhausted')
        key = self.get_edge()
        if isinstance(key, Branch):
            return Action.BRANCH
        return key.action

    def outgoing_type(self) -> type:
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        key = self.get_edge()
        typ = key.typ
        assert isinstance(typ, Typ), typ
        return typ

    def valid_action_type(self, action: str, typ: type = Any):
        assert action in str_transition_map, action
        return action == self.outgoing_action(), typ == self.outgoing_type() or typ is Any

    def progress(self, opt_branch=None):
        if not opt_branch:
            assert len(self.outgoing) == 1


def from_generic_alias(typ: GenericAlias) -> Node:
    stp = STParser(typ=typ)
    return stp.build()


class STParser(NodeVisitor):
    """
    Parses a sessiontype and stores it in a tuple (self.res):
        parsed = STParser("Channel[Recv[str, Offer[Send[bool, End], Loop[Send[int, End]]]]]")
        parsed.res # (recv, (<class 'str'>, (offer, ((send, (<class 'bool'>, end)), (loop, (send, (<class 'int'>, end)))))))
    """

    def __init__(self, src: str = '', typ: GenericAlias = None):
        self.session_tuple = None
        self.id = 0
        if src:
            tree = parse(src)
            self.root = self.new_node()
            self.visit(tree)
        else:
            self.session_tuple = self.from_generic_alias(typ)
        assert self.session_tuple


    
    def get_transition(self, key):
        match key:
            case sessiontype.Send: return Transition(Action.SEND)
            case sessiontype.SendA: return Transition(Action.SEND)
            case sessiontype.Recv: return Transition(Action.RECV)
            case sessiontype.RecvA: return Transition(Action.RECV)
            case sessiontype.Offer: return Transition(Action.BRANCH)
            case sessiontype.OfferA: return Transition(Action.BRANCH)
            case sessiontype.Choose: return Transition(Action.BRANCH)
            case sessiontype.ChooseA: return Transition(Action.BRANCH)
            case sessiontype.Label: return Transition(Action.LABEL)
            case sessiontype.LabelA: return Transition(Action.LABEL)
            case sessiontype.End: return STEnd()


    def from_generic_alias(self, typ: GenericAlias):
        if typ == End:
            return STEnd()
        if isinstance(typ, ForwardRef):
            return typ.__forward_arg__
        base = self.get_transition(typ.__origin__)
        assert isinstance(base, Transition), base
        offset = 0
        if len(typ.__args__) == 3:
            offset = 1
        if base.action in [Action.SEND, Action.RECV]:
            base.typ = typ.__args__[0]
            if offset:
                base.actor = typ.__args__[1].__forward_arg__
            return base, self.from_generic_alias(typ.__args__[1 + offset])
        elif base.action == Action.BRANCH:
            if offset:
                base.actor = typ.__args__[0].__forward_arg__
            ltyp, rtyp = typ.__args__[0+offset], typ.__args__[1+offset]
            base.left  = self.from_generic_alias(ltyp)
            base.right = self.from_generic_alias(rtyp)
            return base
        elif base.action == Action.LABEL:
            if offset:
                base.actor = typ.__args__[1].__forward_arg__
            base.name = typ.__args__[0].__forward_arg__
            base.st = self.from_generic_alias(typ.__args__[1+offset])
            return base





    def next_id(self) -> int:
        res = self.id
        self.id += 1
        return res

    def new_node(self) -> Node:
        return Node(self.next_id())

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
            case 'Channel':
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
        if isinstance(value, Transition):
            if value.action in [Action.SEND, Action.RECV]:
                value.typ = slice[0]
                if len(slice) == 3:
                    value.actor = slice[1]
                    slice = slice[2:][0]
                else:
                    slice = slice[1:][0]
            elif value.action == Action.BRANCH:
                if len(slice) == 3:
                    value.actor = slice[0]
                    slice = slice[1:]
                value.left = slice[0]
                value.right = slice[1]
            elif value.action == Action.LABEL:
                value.name = slice[0]
                if len(slice) == 3:
                    value.actor = slice[1]
                    value.st = slice[2]
                    slice = slice[2:][0]
                else:
                    value.st = slice[1]
                    slice = slice[1:][0]
                    


        if not value:
            self.session_tuple = slice
            return
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
                    nd = new_node()
                    typ = head.typ
                    if isinstance(typ, tuple):
                        head.typ = parameterise(head.typ[0], [head.typ[1]])
                    go(tail,nd)
                    node.outgoing[head] = nd
                    return nd, head
                elif head.action == Action.BRANCH:
                    st1, st2 = head.left, head.right
                    l, r = new_node(), new_node()
                    go(st1, l)
                    go(st2, r)
                    node.outgoing[Branch.LEFT] = l
                    node.outgoing[Branch.RIGHT] = r
                    return l, r
            head = head.__class__
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
        if isinstance(key, Transition | Branch):
            s += f'{key} -> {n.outgoing[key]}'
        elif isinstance(key, typing._GenericAlias):
            typ = key.__args__[0]
            s += f'{key()} {typ} -> {n.outgoing[key]}'
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
    v = from_generic_alias(Recv[int, Recv[int, Send[int, End]]])
    print_node(v)
from ast import *
from typing import TypeVar, Generic, Any
import typing
from sessiontype import Send, Recv, Offer, Choose, End, SessionException
from pydoc import locate
import copy
from collections import deque
from lib import debug_print

A = TypeVar('A')


class TSend(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'send'


class TRecv(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'recv'


class TLabel(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'label'


class TOffer(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'offer'


class TChoose(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'choose'


class STEnd:
    def __str__(self) -> str:
        return 'end'

    def __repr__(self) -> str:
        return self.__str__()


class TEps:
    def __str__(self) -> str:
        return 'ε'

    def __repr__(self) -> str:
        return self.__str__()

class TLeft:
    def __repr__(self) -> str:
        return 'left'

class TRight:
    def __repr__(self) -> str:
        return 'right'

class TGoto:
    def __init__(self, lab) -> None:
        self.lab = lab

    def get_label(self):
        return self.lab

    def __repr__(self) -> str:
        return f'goto {self.lab}'

Transition = TSend | TRecv | TChoose | TOffer | TLabel

str_transition_map = {
    "recv": TRecv,
    "send": TSend,
    "offer": TOffer,
    "choose": TChoose,
}


class Node:
    def __init__(self, id: int, accepting_state: bool = False) -> None:
        self.id = id
        self.accepting = accepting_state
        self.outgoing: dict[TSend | TRecv, Node] = {}

    def __str__(self) -> str:
        state = f'(s{self.id})' if self.accepting else f's{self.id}'
        return state


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

    def outgoing_action(self) -> TSend | TRecv:
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        key = self.get_edge()
        return key.__origin__ 

    def outgoing_type(self) -> type:
        assert len(self.outgoing) == 1, "Function should not be called if it's not a single outgoing edge"
        key = self.get_edge()
        typ = key.__args__[0]
        assert isinstance(typ, type)
        return typ

    def valid_action_type(self, action: str, typ: type=Any):
        assert action in str_transition_map, action
        action = str_transition_map[action]
        return (action == self.outgoing_action(), typ == self.outgoing_type() or typ == None)



def new_node(*args) -> Node:
    return copy.deepcopy(Node(*args))


class STParser(NodeVisitor):
    """
    Parses a sessiontype and stores it in a tuple (self.res):
        parsed = STParser("Channel[Recv[str, Offer[Send[bool, End], Loop[Send[int, End]]]]]")
        parsed.res # (recv, (<class 'str'>, (offer, ((send, (<class 'bool'>, end)), (loop, (send, (<class 'int'>, end)))))))
    """

    def __init__(self, src) -> None:
        self.slcs = deque()
        tree = parse(src)
        self.visit(tree)
        self.session_type = self.slcs[0], self.slcs[1]

    def visit_Name(self, node: Name) -> Any:
        match node.id.lower():
            case 'send':
                return TSend()
            case 'recv':
                return TRecv()
            case 'end':
                return STEnd()
            case 'offer':
                return TOffer()
            case 'choose':
                return TChoose()
            case 'label':
                return TLabel()
            case 'channel':
                return None
            case x:
                return locate(x) or x

    def visit_Tuple(self, node: Tuple) -> Any:
        assert len(node.elts) == 2
        t1 = self.visit(node.elts[0])
        t2 = self.visit(node.elts[1])
        return t1, t2

    def visit_Subscript(self, node: Subscript) -> Any:
        value = self.visit(node.value)
        slice = self.visit(node.slice)
        assert isinstance(slice, tuple)
        self.slcs.appendleft(slice[1])
        self.slcs.appendleft(slice[0])
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

        root = new_node(next_id())
        ref = root


        # (recv, (<class 'str'>, (offer, ((send, (<class 'bool'>, end)), (loop, (send, (<class 'int'>, end)))))))
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
                    #raise SessionException(f'label {lab} not defined here')
            head, tail = tup[0], tup[1]
            head = head.__class__
            if head in [TRecv, TSend]:
                typ = tail[0]
                assert isinstance(typ, type), typ
                nd = new_node(next_id())
                key = head[typ]
                go(tail[1], nd)
                node.outgoing[key] = nd
                return nd, key
            elif head in [TOffer, TChoose]:
                st1, st2 = tail[0], tail[1]
                l, r = new_node(next_id()), new_node(next_id())
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
                    #return labels[tl]
                else:
                    _, key = go(tl, node)
                    return node, key
            else:
                assert head == STEnd or head == str, head
                if head == STEnd:
                    node.accepting = True
                else:
                    return 
                return node, None

        go(self.session_type, ref)
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
        if isinstance(key, typing._GenericAlias):
            typ = key.__args__[0]
            s += f'{key()} {typ} -> {n.outgoing[key]}'
        elif key in [TLeft, TRight]: 
            s += f'{key()} -> {n.outgoing[key]}'
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
    st = STParser('Channel[Send[int, Offer[  Send[str, Recv[str, End]],  Send[int, End]  ]]]')
    print(st.session_type)
    print_node(st.build())
    #st = STParser("Channel[Label['infinity', 'infinity']]()")
    #print_node(st.build())


from ast import *

from typing import TypeVar, Generic, Any
from sessiontype import Send, Recv, Loop, Offer, Choose, End
from pydoc import locate
import copy
from collections import deque

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


class TLoop(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'loop'


class TOffer(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'offer'


class TChoose(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'offer'


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


Transition = TSend | TRecv | TChoose | TOffer | TLoop


class Node:
    def __init__(self, id: int, accepting_state: bool = False) -> None:
        self.id = id
        self.accepting = accepting_state
        self.outgoing: dict[TSend | TRecv, Node] = {}

    def __str__(self) -> str:
        state = f'(s{self.id})' if self.accepting else f's{self.id}'
        return state

    def is_valid_transition(self, op : str, typ: type = None) -> bool:

        op = get_op(op)
        if typ is None:
            return op[int] in self.outgoing or op[str] in self.outgoing or op[bool] in self.outgoing
        else:
            return op[typ] in self.outgoing

    def get_edge(self, op, typ = None):
        op = get_op(op)
        if typ is None:
            if op[int] in self.outgoing :
                 typ = int
            elif op[str] in self.outgoing:
                typ = str
            elif op[bool] in self.outgoing:
                typ = bool

            return self.outgoing[op[typ]]

        else:
            return self.outgoing[op[typ]]



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
            case 'choice':
                return TChoose()
            case 'loop':
                return TLoop()
            case 'channel':
                return None
            case x:
                return locate(x)

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
        def go(tup, node: Node):
            if isinstance(tup, STEnd):
                node.accepting = True
                return node, None
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
                n1, k1 = go(st1, node)
                n2, k2 = go(st2, node)
                node.outgoing[k1] = n1
                node.outgoing[k2] = n2
                return None
            elif head in [TLoop]:
                _, key = go(tail, node)
                node.outgoing[key] = node
                return node, key
            else:
                assert head == STEnd, head
                node.accepting = True
                return node, None

        go(self.session_type, ref)
        return root

    def pp(self):
        def aux(st, indent=0):
            indent_size = 2
            if isinstance(st, type):
                print(' ' * indent, st)
                return
            head = st[0]
            tail = st[1]
            print(' ' * indent, head)
            if head in [TOffer, TChoose]:
                indent = indent_size + indent
                print(' ' * indent, 'left')
                aux(tail[0], indent)
                print(' ' * indent, 'right')
                aux(tail[1], indent)
            else:  # [TSend, TRecv, TLoop]
                aux(tail, indent + indent_size)

        aux(self.session_type, 0)

def get_op(op : str):
    match str.lower(op):
        case 'recv':
            return TRecv
        case 'send':
            return TSend
        case x:
            raise Exception(f'unsupported type {x}')

def session_type_from_tuple(t):
    if isinstance(t, tuple):
        head, tail = t[0], t[1]
        head = head.__class__
        if head == TLoop:
            st = session_type_from_tuple(tail)
            return Loop[st]
        elif head in [TSend, TRecv]:
            typ = tail[0]
            assert isinstance(typ, type)
            st = session_type_from_tuple(tail[1])
            return (Send if head == TSend else Recv)[typ, st]
            st1 = sessiontype_from_(tail[0])
            st1 = session_type_from_tuple(tail[0])
            st2 = session_type_from_tuple(tail[1])
            return (Offer if head == TOffer else Choose)[st1, st2]
        else:
            raise Exception("unhandled sessiontype:", head)
    else:
        assert isinstance(t, STEnd)
        return End


def print_node(n: Node):
    if not n.outgoing:
        return
    print(n)
    for key in n.outgoing:
        typ = key.__args__[0]
        print(key(), typ, '->', n.outgoing[key])
    print()
    for key in n.outgoing:
        n1 = n.outgoing[key]
        if n1.id != n.id:
            print_node(n1)


if __name__ == '__main__':
    send_int_recv_str_end = "Channel[Send[int, Recv[str, End]]]"
    send_int_recv_bool_send_float_recv_str_end = "Channel[Send[int, Recv[bool, Send[float, Recv[str, End]]]]]"
    send_int_recv_bool_offer___send_float_recv_str_end___recv_bool_end = "Channel[Send[int, Recv[bool, Offer[ Send[float, Recv[str, End]], Recv[bool, End]]]]]"
    offer___send_int_end___recv_str_end = "Channel[Offer[Send[int, End], Recv[str, End]]]"
    offer___offer___send_int_end___send_bool_end___recv_str_end = "Channel[Offer[ Offer[Send[int,End], Send[bool, End]], Recv[str, End]]]"
    # offer___loop_start_offer___send_int_end___send_bool_end_loop_end__recv_str_end = "Channel[Offer[ Loop[Offer[Send[int,End], Send[bool, End]]], Recv[str, End]]]"

    sts = [send_int_recv_str_end, send_int_recv_bool_send_float_recv_str_end, offer___send_int_end___recv_str_end,
           send_int_recv_bool_offer___send_float_recv_str_end___recv_bool_end,
           offer___offer___send_int_end___send_bool_end___recv_str_end]
    for s in sts:
        print(s)
        sm: Node = STParser(s).build()
        print(sm, end='\n\n')

    send_int_recv_str_end = "Channel[Send[int, Send[bool, Recv[str, End]]]]"
    loop_send_int_end = "Channel[Loop[Send[int, End]]]"
    recv_str_offer___send_bool_end___loop_send_int_end = "Channel[Recv[str, Offer[Send[bool, End], Loop[Send[int, End]]]]]"
    offer___send_int_end___recv_str_end = "Channel[Offer[Send[int, End], Recv[str, End]]]"

    res = STParser(send_int_recv_str_end).build()
    print_node(res)

    print('-')
    res = STParser(offer___send_int_end___recv_str_end).build()
    print_node(res)

    print('-')
    builder = STParser(loop_send_int_end).build()
    print_node(res)

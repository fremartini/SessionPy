from ast import *

from typing import TypeVar, Generic, Any, Union
from sessiontype import Send, Recv, Loop, Offer, Choose, End
from channel import Channel
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


class STEnd():
    def __str__(self) -> str:
        return 'end'

    def __repr__(self) -> str:
        return self.__str__()


class TEps():
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

    def get_id(self) -> int:
        res = self.id
        self.id += 1
        return res

    def __str__(self) -> str:
        state = f'(s{self.id})' if self.accepting else f's{self.id}'
        return state
    # def __str__(self) -> str:
    #     state = f'(s{self.id})' if self.accepting else f's{self.id}'
    #     res = state
    #     keys = list(self.outgoing.keys())
    #     def S(key) -> str:
    #         transition = str(key).split('.')[1]
    #         state = str(self.outgoing[key]).strip()
    #         value = f'({state})' if self.accepting else state
    #         return f' --[{transition}]--> {value}'

    #     if len(keys) > 0:
    #         if len(keys) > 1:
    #             res += ' -> &['
    #             i = 0
    #             while i < len(keys)-1:
    #                 res += f'{state}{S(keys[i])}, '
    #                 i += 1
    #             res += f'{state}{S(keys[i])}]'
    #         else:
    #             key = keys[0]
    #             if self.outgoing[key].id == self.id:
    #                 transition = str(key).split('.')[1]
    #                 res += f' --[{transition}]--> {state}'
    #             else:
    #                 res += f'{S(key)}'
    #     return res


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
        self.res = self.slcs[0], self.slcs[1]

    def visit_Name(self, node: Name) -> Any:
        res = None
        match node.id.lower():
            case 'send':
                res = TSend()
            case 'recv':
                res = TRecv()
            case 'end':
                res = STEnd()
            case 'offer':
                res = TOffer()
            case 'choice':
                res = TChoose()
            case 'loop':
                res = TLoop()
            case 'channel':
                res = None
            case x:
                res = locate(x)
        return res

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


def pp(st, indent=0):
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
        pp(tail[0], indent)
        print(' ' * indent, 'right')
        pp(tail[1], indent)
    else:  # [TSend, TRecv, TLoop]
        pp(tail, indent + indent_size)


def sessiontype_from_tuple(t):
    if isinstance(t, tuple):
        head, tail = t[0], t[1]
        head = head.__class__
        if head == TLoop:
            st = sessiontype_from_tuple(tail)
            return Loop[st]
        elif head in [TSend, TRecv]:
            typ = tail[0]
            assert isinstance(typ, type)
            st = sessiontype_from_tuple(tail[1])
            return (Send if head == TSend else Recv)[typ, st]
            st1 = sessiontype_from_(tail[0])
            st1 = sessiontype_from_tuple(tail[0])
            st2 = sessiontype_from_tuple(tail[1])
            return (Offer if head == TOffer else Choose)[st1, st2]
        else:
            raise Exception("unhandled sessiontype:", head)
    else:
        assert isinstance(t, STEnd)
        return End


def build(st):
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

    go(st, ref)
    return root


def _driver_code():
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
        sm: STParser = STParser(s)
        st = sm.slcs[0], sm.slcs[1]
        print(build(st), end='\n\n')


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


send_int_recv_str_end = "Channel[Send[int, Send[bool, Recv[str, End]]]]"
loop_send_int_end = "Channel[Loop[Send[int, End]]]"
recv_str_offer___send_bool_end___loop_send_int_end = "Channel[Recv[str, Offer[Send[bool, End], Loop[Send[int, End]]]]]"
offer___send_int_end___recv_str_end = "Channel[Offer[Send[int, End], Recv[str, End]]]"

builder = STParser(send_int_recv_str_end)
res = build(builder.res)
print_node(res)

print('-')
builder = STParser(offer___send_int_end___recv_str_end)
res = build(builder.res)
print_node(res)

print('-')
builder = STParser(loop_send_int_end)
res = build(builder.res)
print_node(res)
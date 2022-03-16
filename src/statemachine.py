from ast import *

from typing import TypeVar, Generic, Any
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


class TChoice(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'offer'


class STEnd:
    def __str__(self) -> str:
        return 'end'

    def __repr__(self) -> str:
        return self.__str__()



class Node:
    def __init__(self, id: int, accepting_state: bool = False) -> None:
        self.id = id
        self.accepting = accepting_state
        self.outgoing: dict[TSend | TRecv, Node] = {}

    def __str__(self) -> str:
        res = f'(s{self.id})' if self.accepting else f's{self.id}'
        keys = list(self.outgoing.keys())

        def S(key) -> str:
            transition = str(key).split('.')[1]
            state = str(self.outgoing[key]).strip()
            value = f'({state})' if self.accepting else state
            return f' --[{transition}]--> {value}'

        if len(keys) > 0:
            if len(keys) > 1:
                res += ' -> &['
                i = 0
                while i < len(keys) - 1:
                    res += f'{S(keys[i])}, '
                    i += 1
                res += f'{S(keys[i])}]'
            else:
                res += f'{S(keys[0])}'
        return res


def new_node(*args) -> Node:
    return copy.deepcopy(Node(*args))


class SMBuilder(NodeVisitor):

    def __init__(self, tree) -> None:
        self.slcs = deque()
        print(dump(tree, indent=2))
        self.visit(tree)
        self.st = (self.slcs[0], self.slcs[1])

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

        transition = TSend | TRecv | TChoice | TOffer
        first = type | transition
        second = tuple | STEnd

        def go(st: STEnd | tuple[first, second], r: Node):

            if isinstance(st, STEnd):
                r.accepting = True
                return

            assert isinstance(st, tuple), st

            head = st[0]
            tail = st[1]

            assert isinstance(head, first), head
            assert isinstance(tail, second), tail

            if tail == STEnd:
                r.accepting = True
                return

            if isinstance(head, TSend | TRecv):
                assert isinstance(tail, tuple), tail
                m = new_node(next_id())
                typ = tail[0]
                tr = (TSend if isinstance(head, TSend) else TRecv)[typ]
                r.outgoing[tr] = m
                r = m
                go(tail[1], r)
                return tr, r
            elif isinstance(head, TOffer | TChoice):
                assert isinstance(tail, tuple), tail

                left = tail[0]
                right = tail[1]

                assert isinstance(left, tuple), left
                assert isinstance(right, tuple), right

                t1, m = go(left, r)
                t2, n = go(right, r)
                assert str(t1()) in ["send", "recv"], t1
                assert str(t2()) in ["send", "recv"], t2
                r.outgoing[t1] = m
                r.outgoing[t2] = n
                return t1, t2  # TODO: Investigate

        go(self.st, ref)
        return root

    def visit_Name(self, node: Name) -> Any:
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
                res = TChoice()
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

    def pp(self):
        def aux(st, indent=0):
            indent_size = 2
            if isinstance(st, type):
                print(' ' * indent, st)
                return
            head = st[0]
            tail = st[1]
            print(' ' * indent, head)
            if head in [TOffer, TChoice]:
                indent = indent_size + indent
                print(' ' * indent, 'left')
                aux(tail[0], indent)
                print(' ' * indent, 'right')
                aux(tail[1], indent)
            else:  # [TSend, TRecv, TLoop]
                aux(tail, indent + indent_size)

        aux(self.st, 0)


def _driver_code():
    send_int_recv_str_end = "Channel[Send[int, Recv[str, End]]]"
    send_int_recv_bool_send_float_recv_str_end = "Channel[Send[int, Recv[bool, Send[float, Recv[str, End]]]]]"
    send_int_recv_bool_offer___send_float_recv_str_end___recv_bool_end = "Channel[Send[int, Recv[bool, Offer[ Send[float, Recv[str, End]], Recv[bool, End]]]]]"
    offer___send_int_end___recv_str_end = "Channel[Offer[Send[int, End], Recv[str, End]]]"
    offer___offer___send_int_end___send_bool_end___recv_str_end = "Channel[Offer[ Offer[Send[int,End], Send[bool, End]], Recv[str, End]]]"
    # offer___loop_start_offer___send_int_end___send_bool_end_loop_end__recv_str_end = "Channel[Offer[ Loop[Offer[Send[int,End], Send[bool, End]]], Recv[str, End]]]"

    sts = [send_int_recv_str_end]
    for s in sts:
        a = parse(s)
        graph = SMBuilder(a).build()
        print(graph, end='\n\n')


if __name__ == '__main__':
    _driver_code()

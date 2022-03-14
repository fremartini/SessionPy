from ast import *

from typing import TypeVar, Generic, Any
from sessiontype import Send, Recv, End
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
class TChoice(Generic[A]):
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


_ID = 0
def get_id() -> int:
    global _ID
    res = _ID
    _ID += 1
    return res


#Node
# s0
# accepting
# outgoing
# { TSend[int] -> s1 }

#Node
# s1
# accepting
# outgoing
# { TRecv[str] -> s2 }


#Node
# s2
# accepting = True
# outgoing
# { }




class Node:
    def __init__(self, accepting_state: bool=False) -> None:
        self.id = get_id()
        self.accepting = accepting_state
        self.outgoing = {}


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
                while i < len(keys)-1:
                    res += f'{S(keys[i])}, '
                    i += 1
                res += f'{S(keys[i])}]'
            else:
                res += f'{S(keys[0])}'
        return res
        

def new_node(*args) -> Node:
    return copy.deepcopy(Node(*args))

class SMBuilder(NodeVisitor):
    
    def __init__(self, src) -> None:
        self.DEBUG = False # TODO: Remove
        self.vals = deque()
        self.slcs = deque()
        self.idents = 0
        tree = parse(src)
        self.res = self.visit(tree)
        if self.DEBUG:
            print('# Parsing done:')
            print('Values')
            for val in self.vals:
                print('  -', val)
            print('Slices')
            for val in self.slcs:
                print('  -', val)
                
        
    
    def P(self, *args):
        print(self.idents * "  ", end='')
        for arg in args:
            print(str(arg), end = ' ')
        print()

    def push(self):
        self.idents += 1

    def pop(self):
        self.idents -= 1


    def visit_Name(self, node: Name) -> Any:
        res = None
        match node.id.lower():
            case 'send': res = TSend()
            case 'recv': res = TRecv()
            case 'end': res = STEnd()
            case 'offer': res = TOffer()
            case 'choice': res = TChoice() 
            case 'loop': res = TLoop()
            case 'channel': res = None
            case x: res = locate(x)
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
        print(' '*indent, st)
        return
    head = st[0]
    tail = st[1]
    print(' '*indent, head)
    if head in [TOffer, TChoice]:
        indent = indent_size + indent
        print(' '*indent, 'left')
        pp(tail[0], indent)
        print(' '*indent, 'right')
        pp(tail[1], indent)
    else: #[TSend, TRecv, TLoop]
        pp(tail, indent+indent_size)

# (offer, ((send, (<class 'int'>, end)), (recv, (<class 'str'>, end))))
def build(st):
    root = new_node()
    ref = root
    def go(st, r):
        if isinstance(st, STEnd):
            r.accepting = True
            return r
        if isinstance(st, TSend | TRecv):
            return st
        # (send, (int, (recv, (str, end)))
        print('st', st)
        action = st[0] # send, offer, recv
        m = new_node()
        if isinstance(action, TSend | TRecv):
            typ = st[1][0] # int
            transition = (TSend if isinstance(action, TSend) else TRecv)[typ]
            r.outgoing[transition] = m
            r = m
            return transition, go(st[1][1], r)
        elif isinstance(action, TOffer | TChoice):
            # (offer, 1: ( 0: (send, (<class 'int'>, end)), 1: (recv, (<class 'str'>, end))))
            left = st[1][0]
            right = st[1][1]
            t1, st1 = go(left, m)
            t2, st2 = go(right, m)
            print('t1, st1', t1, st1)
            print('t2, st2', t2, st2)
            assert str(t1()) in ["send", "recv"]
            assert str(t2()) in ["send", "recv"]
            r.outgoing[t1] = st1
            r.outgoing[t2] = st2
            return t1, st1
            
    go(st, ref)
    return root

send_int_recv_str_end = "Channel[Send[int, Recv[str, End]]]"
send_int_recv_bool_send_float_recv_str_end = "Channel[Send[int, Recv[bool, Send[float, Recv[str, End]]]]]"
offer___send_int_end___recv_str_end = "Channel[Offer[Send[int, End], Recv[str, End]]]"
offer___offer___send_int_end___send_bool_end___recv_str_end = "Channel[Offer[ Offer[Send[int,End], Send[bool, End]], Recv[str, End]]]"
offer___loop_start_offer___send_int_end___send_bool_end_loop_end__recv_str_end = "Channel[Offer[ Loop[Offer[Send[int,End], Send[bool, End]]], Recv[str, End]]]"



sm : SMBuilder = SMBuilder(offer___send_int_end___recv_str_end)

st = sm.slcs[0], sm.slcs[1]
print(st)

nd = build(st)
print(nd)
"""
X[Y]
Module(body=[Expr(value=Subscript(value=Name(id='Channel', ctx=Load()),
    slice=Subscript(value=Name(id='Send', ctx=Load()),
        slice=Tuple(elts=[Name(id='int', ctx=Load()),
            Subscript(value=Name(id='Recv', ctx=Load()),
                slice=Tuple(elts=[Name(id='str', ctx=Load()), Name(id='End',
                    ctx=Load())], ctx=Load()), ctx=Load())], ctx=Load()),
                ctx=Load()), ctx=Load()))], type_ignores=[])

Module(body=[Expr(value=Subscript(value=Name(id='Channel', ctx=Load()),
    slice=Subscript(value=Name(id='Offer', ctx=Load()),
        slice=Tuple(elts=[Subscript(value=Name(id='Offer', ctx=Load()),
            slice=Tuple(elts=[Subscript(value=Name(id='Send', ctx=Load()),
                slice=Tuple(elts=[Name(id='int', ctx=Load()), Name(id='End',
                    ctx=Load())], ctx=Load()), ctx=Load()),
                Subscript(value=Name(id='Send', ctx=Load()),
                    slice=Tuple(elts=[Name(id='bool', ctx=Load()),
                        Name(id='End', ctx=Load())], ctx=Load()), ctx=Load())],
                    ctx=Load()), ctx=Load()), Subscript(value=Name(id='Recv',
                        ctx=Load()), slice=Tuple(elts=[Name(id='str',
                            ctx=Load()), Name(id='End', ctx=Load())],
                            ctx=Load()), ctx=Load())], ctx=Load()),
                        ctx=Load()), ctx=Load()))], type_ignores=[])

# Offer example
Subscript
    Value: "Channel"
    Slice: 
        Subscript
            Value: "Offer"
            Slice:
                Tuple
                    1: Subscript
                        Value: "Offer"
                        Slice:
                            Tuple
                                1: 


# Simple example
Subscript
    Value: "Channel"
    Slice: 
        Subscript:
            Value: "Send"
            Slice:
                Tuple:
                    1: "int"
                    2: Subscript
                        Value: "Recv"
                        Slice: 
                            Tuple:
                                1: "str"
                                2: "end"




"""
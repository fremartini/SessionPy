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
        return f'[send]'
class TRecv(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()
    def __str__(self) -> str:
        return f'[recv]'

class TLoop(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()
    def __str__(self) -> str:
        return f'[loop]'



class TOffer(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()
    def __str__(self) -> str:
        return f'[offer]'
class TChoice(Generic[A]):
    def __repr__(self) -> str:
        return self.__str__()
    def __str__(self) -> str:
        return f'[offer]'


class STEnd:
    def __str__(self) -> str:
        return '[end]'


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
        if len(self.outgoing) > 0:
            for key in self.outgoing:
                if not key:
                    continue
                transition = str(key).split('.')[1]
                state = str(self.outgoing[key]).strip()
                value = f'({state})' if self.accepting else state
                res += f' --[{transition}]--> {value}'
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
            case 'send': res = TSend
            case 'recv': res = TRecv
            case 'end': res = STEnd
            case 'offer': res = TOffer
            case 'choice': res = TChoice 
            case 'loop': res = TLoop 
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

#(SEND, (int, (recv, str)))
def build(st):
    root = new_node()
    ref = root
    def go(st, r):
        if st == STEnd:
            r.accepting = True
            return
        # (send, (int, (recv, (str, end)))
        action = st[0] # send
        typ = st[1][0] # int
        m = new_node()
        transition = action[typ]
        r.outgoing[transition] = m
        r = m
        go(st[1][1], r) 
    go(st, ref)
    return root

send_int_recv_str_end = "Channel[Send[int, Recv[str, End]]]"
send_int_recv_bool_send_float_recv_str_end = "Channel[Send[int, Recv[bool, Send[float, Recv[str, End]]]]]"
offer___send_int_end___recv_str_end = "Channel[Offer[Send[int, End], Recv[str, End]]]"
offer___offer___send_int_end___send_bool_end___recv_str_end = "Channel[Offer[ Offer[Send[int,End], Send[bool, End]], Recv[str, End]]]"
offer___loop_start_offer___send_int_end___send_bool_end_loop_end__recv_str_end = "Channel[Offer[ Loop[Offer[Send[int,End], Send[bool, End]]], Recv[str, End]]]"

sm : SMBuilder = SMBuilder(send_int_recv_bool_send_float_recv_str_end)

st = sm.slcs[0], sm.slcs[1]
#print(st)

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
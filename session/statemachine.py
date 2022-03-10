from ast import *

from typing import TypeVar, Generic, Any
from sessiontype import Send, Recv, End
from channel import Channel
from pydoc import locate
import copy
from collections import deque
A = TypeVar('A')

class TSend(Generic[A]):
    def __str__(self) -> str:
        return f'[send]'

class TRecv(Generic[A]):
    def __str__(self) -> str:
        return f'[recv]'

class TOffer(Generic[A]):
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
        

def newNode(*args) -> Node:
    return copy.deepcopy(Node(*args))
class SMBuilder(NodeVisitor):
    
    def __init__(self, src) -> None:
        tree = parse(src)
        self.ref = newNode()
        self.root = self.ref
        self.type_queue = deque()
        self.ops = deque()
        self.visit(tree)
        print('# Finished processing type:')
        print('operations ->', self.ops)
        print('types ->', self.type_queue)
        print("###########################")


    def visit_Name(self, node: Name) -> Any:
        match node.id.lower():
            case 'send': return TSend
            case 'recv': return TRecv
            case 'end': return STEnd
            case 'offer': return TOffer
            case 'channel': return None
            case x: return locate(x)
        
    def visit_Tuple(self, node: Tuple) -> Any:
        for elem in node.elts:
            val = self.visit(elem)
            if val:
                self.type_queue.append(val)
        
    
    def visit_Subscript(self, node: Subscript) -> Any:
        slice = self.visit(node.slice)
        value = self.visit(node.value)
        if value:
            # FIXME: Buggy. Need a sane way to add Offers into the data structure
            # Examples:
            # Offer[Send[int, End], Recv[str, End]] => [offer, send, recv]
            # Offer[Offer[Send[bool, Recv[str, End]], Recv[int, Recv[bool, End]]]] => [offer, offer, send, 
            add = self.ops.appendleft if value in [TOffer] else self.ops.appendleft
            add(value)

def is_transition(trans):
    return trans in [TSend, TRecv, TOffer]

send_int_recv_str_end = "Channel[Send[int, Recv[str, End]]]"
offer___send_int_end___recv_str_end = "Channel[Offer[Send[int, End], Recv[str, End]]]"
offer___offer___send_int_end___send_bool_end___recv_str_end = "Channel[Offer[Offer[Send[int,End], Send[bool, End]], Recv[str, End]]]"

sm : SMBuilder = SMBuilder(offer___offer___send_int_end___send_bool_end___recv_str_end)

ops, typs = sm.ops, sm.type_queue

def build_sm(ops, typs):
    root = Node()
    ref: Node = root

    def go(ops, typs, ref):
        if not ops:
            return

        op = ops.popleft()

        if op in [TOffer]:
            ...
        elif op in [TSend, TRecv]:
            typ = typs.popleft()
            print('typ', typ)
            transition = op[typ]
            accepting = typs[0] == STEnd
            next_node: Node = newNode()
            ref.outgoing[transition] = next_node
            ref = next_node
            if accepting:
                print('node', ref.id, 'is accepting')
                print(ref)
                ref.accepting = accepting
        go(ops, typs, ref)
    go(ops, typs, ref)
    return root
    ...


sm1 = build_sm(ops, typs)
print(sm1)

 
# operations, types = sm.ops, sm.type_queue
# root = newNode()
# def build_sm(operations, types):
#     if not operations:
#         return (0,0)
# 
#     print(operations, types)
#     if operations[-1] == TOffer:
#         operations.pop()
#         transition1, _ = build_sm(operations, types)
#         transition2, _ = build_sm(operations, types)
#         n = newNode()
#         if not operations:
#             n.accepting = True
#         root.outgoing[transition1] = n
#         root.outgoing[transition2] = n
#         return TOffer, root
#     elif operations[0] in [TSend, TRecv]:
#         n = newNode()
#         op = operations.pop(0)
#         if not operations:
#             n.accepting = True
#         transition, _ = build_sm(operations, types)
#         root.outgoing[transition] = n
#         typ = types.get()
#         return op[typ], root
#     else:
#         raise Exception('eh', operations, types)
# 
# 
# 
#     
# _,what = build_sm(operations, types) 
# print(what)
# 
# 
# """
#     tr = [
#         (0, TSend[int], 1),
#         (1, TRecv[str], 2),
#         (2, End, 2)
#     ]
# 
#     Graph.of_list(tr)
# 
#      <SUBSCRIPT>
#    value= <class 'channel.Channel'>
#    <SUBSCRIPT>
#      value= <class '__main__.TSend'>
#      <TUPLE>
#        <SUBSCRIPT>
#          value= <class '__main__.TRecv'>
#          <TUPLE>
#            <class 'str'>
#            <class '__main__.STEnd'>
#            </TUPLE>
#          slice= [<class 'str'>, <class '__main__.STEnd'>]
#          </SUBSCRIPT>
#        <class 'int'>
#        None
#        </TUPLE>
#      slice= [<class 'int'>, None]
#      </SUBSCRIPT>
#    slice= None
#    </SUBSCRIPT>
# """

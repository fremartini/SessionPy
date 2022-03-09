from ast import *

from typing import TypeVar, Generic, Any
from sessiontype import Send, Recv, End
from channel import Channel
from pydoc import locate
import copy

A = TypeVar('A')

class TSend(Generic[A]):
    def __str__(self) -> str:
        return f'[send]'

class TRecv(Generic[A]):
    def __str__(self) -> str:
        return f'[recv]'

class TEnd:
    def __str__(self) -> str:
        return '[end]'


_ID = 0
def get_id() -> int:
    global _ID
    id = _ID
    _ID += 1
    return id

def wrap_parens(s: str) -> str:
    return f'({s})'

    
class Node:
    def __init__(self, accepting_state: bool=False, transitions={}) -> None:
        self.id = get_id()
        self.accepting = accepting_state
        self.transitions = transitions


    def __str__(self) -> str:
        res = f's{self.id} '
        if self.transitions:
            for key in self.transitions:
                if not key: continue
                transition = str(key).split('.')[1]
                value = wrap_parens(str(self.transitions[key])) if self.accepting else str(self.transitions[key])
                res += f'--[{transition}]--> {value}'
        return res
        

class SMBuilder(NodeVisitor):
    
    def __init__(self, src) -> None:
        tree = parse(src)
        self.node = Node()
        self.graph = self.node.transitions
        self.indent = 0
        self.debug = False
        self.visit(tree)

    def indents(self) -> str:
        return "  " * self.indent


    def visit_Name(self, node: Name) -> Any:
        match node.id.lower():
            case 'send': return TSend
            case 'recv': return TRecv
            case 'end': return TEnd
            case 'channel': return Channel
            case x: return locate(x)
        
    def visit_Tuple(self, node: Tuple) -> Any:
        if self.debug: print(self.indents(), '<TUPLE>')
        self.indent += 1
        processed_elems = [self.visit(elem) for elem in node.elts]
        if self.debug:
            for pe in processed_elems:
                print(self.indents(), pe)
            print(self.indents(), '</TUPLE>')
        self.indent -= 1
        return processed_elems
    
# sm : SMBuilder = SMBuilder("Channel[Send[int, Recv[str, End]]]")
    def visit_Subscript(self, node: Subscript) -> Any:
        # print(dump(node))
        if self.debug: print(self.indents(), '<SUBSCRIPT>')
        self.indent += 1
        value = self.visit(node.value)
        if self.debug: print(self.indents(), 'value=', value)
        slc = self.visit(node.slice)
        if self.debug: print(self.indents(), 'slice=', slc)
        if value in [TSend, TRecv]:
            assert type(slc[0]) == type
            next_node = Node(slc[1] == TEnd) # Is accepting state if Slice has End
            transition = value[slc[0]]
            self.graph[transition] = copy.deepcopy(next_node)
            self.graph = next_node.transitions
        elif value == TEnd:
            print('subscript: mark current node as DONE')

        else:
            assert value == Channel

        if self.debug: print(self.indents(), '</SUBSCRIPT>')
        self.indent -= 1


    
        
"Channel[(Send, int), [(Recv, str), [(End, None)]]]"
"Channel[Send[int, Recv[str, End]]]"

sm : SMBuilder = SMBuilder("Channel[Send[int, Recv[str, End]]]")
print(sm.node)

class LinkedList:

    def __init__(self, value) -> None:
        self.value = value
        self.next = None
        pass

    def __str__(self) -> str:
        res = str(self.value)
        if self.next:
            res += ' -> '
            res += str(self.next)
        return res

root = LinkedList(1)
root.next = LinkedList(2)
next = root.next
next.next = LinkedList(3)

#print(root)
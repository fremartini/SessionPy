
# Channel[ Choice[
#             Send[int, End], 
#             Recv[str, Choice[
#                             Send[int, End], 
#                             Loop[Recv[str,End]]
#                         ]
#                 ]
#             ]
#         ]

# Channel [Send[int, Recv[str, End]]]

# Channel [Loop[Send[int, End]]]

from ast import *

from typing import TypeVar, Generic, Any
from sessiontype import Send, Recv, End
from channel import Channel
from pydoc import locate

A = TypeVar('A')

class TSend(Generic[A]):
    ...

class TRecv(Generic[A]):
    ...

class TEnd():
    ...


_ID = 0
def get_id() -> int:
    global _ID
    id = _ID
    _ID += 1
    return id
    
class Node:
    def __init__(self, terminal: bool=False, transitions = {}) -> None:
        self.id = get_id()
        self.terminal = terminal
        self.transitions = transitions

    def __str__(self) -> str:
        res = f'Node #{self.id}, terminal = {self.terminal} '
        if self.transitions:
            res += '{'
            for key in self.transitions:
                res += f'  {key} -> {self.transitions[key]}'
            res += '}'
        return res
        
"""

{
    TSend[int]: Node at 0000x123
    TSend[bool]: Node at 0000x124
}

"""

def read_src_from_file(file) -> str:
    with open(file, 'r') as f:
        return f.read()


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

    # Subscript(expr value, expr slice, expr_context)
    # Subscript(value=Name(id='Channel', ctx=Load()),
            # slice=Subscript(value=Name(id='Send', ctx=Load()),
                # slice=Tuple(elts=[Name(id='int', ctx=Load()),
                    # Subscript(value=Name(id='Recv', ctx=Load()),
                        # slice=Tuple(elts=[Name(id='str', ctx=Load()),
                            # Name(id='End', ctx=Load())], ctx=Load()),
                        # ctx=Load())], ctx=Load()), ctx=Load()), ctx=Load())

    # Can be any of: Channel, Send, Recv, int, str, ...
    def visit_Name(self, node: Name) -> Any:
        match node.id.lower():
            case 'send': return TSend()
            case 'recv': return TRecv()
            case 'end': return TEnd()
            case x: return locate(x)
        
        
        
    # Tuple(expr* elts, expr_context ctx)
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
    
    def visit_Subscript(self, node: Subscript) -> Any:
        # print(dump(node))
        if self.debug: print(self.indents(), '<SUBSCRIPT>')
        self.indent += 1
        self.current_node = Node()
        value = self.visit(node.value)
        if self.debug: print(self.indents(), 'value=', value)
        slc = self.visit(node.slice)
        if self.debug: print(self.indents(), 'slice=', slc)
        if isinstance(value, TSend):
            assert type(slc[0]) == type
            print('TRANSITION', value[slc[0]])
        print('subcript value', value)
        match value:
            case TEnd:
                self.current_node.is_terminal = True
        if self.debug: print(self.indents(), '</SUBSCRIPT>')
        self.indent -= 1

    
        
"Channel[(Send, int), [(Recv, str), [(End, None)]]]"
"Channel[Send[int, Recv[str, End]]]"

sm : SMBuilder = SMBuilder("Channel[Send[int, Recv[str, End]]]")
print(sm.node)
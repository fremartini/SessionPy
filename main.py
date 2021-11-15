from typing import TypeVar
from channel import *
from protocol import *
from enum import Enum

"""
PSEUDO TIME
^^^^^^^^^^^

ch = Channel(roleA, roleB, int!int?bool?)

-> corresponds to ->
roleA:
send int
recv int
recv bool

roleB:
recv int
send int
send bool

"""


"""
// type ST =
    Send of Basic
    Recv of Basic
and Basic =
    Int
    | Str
    | Custom of Object
    [send(int), recv(str)]

def send(typ) -> type:
    sendTyp = TypeVar(f'Send{typ}')
    return sendTyp


"""


"""
It starts by specifying the intended interactions (choreography) 
as a global protocol in the protocol description language Scribble.  <---- GLOBAL PROTOC

Then Scribble local protocols are generated mechanically for each 
participant (role) defined in the protocol.                          <---- LOCAL PROTOC

After that processes for each role are implemented using MPST        <---- FSM
operations exposed by Python conversation library. 
An external monitor is assigned to each endpoint. During communication 
initiation the monitor retrieves the local protocol for its 
process and converts it to a finite state machine (FSM).

The FSM continuously checks at runtime that each interaction         <---- VERIFY PROTOC RUNTIME
(execution trace) is correct.
"""
if __name__ == '__main__':
    pass
    #Protocol().projectFile("proto.p")

def typToStr(typ): 
    return str(typ).split('\'')[1]

def send(t : type) -> type:
    return typ(t, "send")

def recv(t : type) -> type:
    return typ(t, "recv")

def typ(t : type, prefix : str) -> type:
    typStr = typToStr(typ)
    prefix_typStr = TypeVar(f'{prefix}_{typStr}')
    return prefix_typStr

class Op(Enum):
    SEND = 1
    RECV = 2
    END = 3

class SessionType:
    def __init__(self, op : Op, typ : type, rest) -> None:
        self.t = (op, typ, rest)

Protocol("B1 -> S : str; S -> B1 : int; S -> B2 : int; B1 -> B2: int; B2 -> S: str;")
Channel(SessionType(Op.SEND, int, SessionType(Op.RECV, int, SessionType(Op.END, None, None))), 5000)

"""
// glo spec
p = Protocol(A->B:int,B->A:str)
=> ch

// local spec
// A's POV
ch = Channel(T)
T = !int.?str.end

// B's POV
ch = Channel(T)
T = ?int.!str.end
ch.send(true)


K ::=
    End
    type K

T ::=
    T OP 
    

OP ::=
    !
    ?
    

"""
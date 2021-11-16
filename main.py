from channel import *
from protocol import *
from sessionType import *

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

"""
global:
    B1 -> S : str; 
    S -> B1 : int; 
    S -> B2 : int;
    B1 -> B2: int; 
    B2 -> S: str;

local:
B1: 
    S : !str; 
    S : ?int; 
    B2 : !int;
B2:
    S : ?int
    B1 : ?int
    S : !int
S: 
    B1 : ?str;
    B1 : !int;
    B2 : !int;
    B2 : ?str;
"""

if __name__ == '__main__':
    proto = "B1 -> S : str; S -> B1 : int; S -> B2 : int; B1 -> B2: int; B2 -> S: str;"

    p = Protocol(proto)
    print(p.projectGlobalProtocol())

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
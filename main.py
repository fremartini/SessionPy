from channel import *
from conversation import Conversation
from sessiontype import *

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

global:
    B1 -> S : str; 
    S -> (B1, B2) : int; 
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
    pass

class BaseConversation():
    c = Conversation.create("B1 -> S : str; S -> B1 : int; S -> B2 : int; B1 -> B2: int; B2 -> S: str;", 'config.yml')

class S(BaseConversation):
    @checkLocalProtocol
    def run():
        c : Conversation = super.c
        c.join('S', 'serv')

        c.recv('B1')
        c.send('B1', 12)


        c.send('B2', 12)
        c.recv('B2')

        c.stop()

class B1(BaseConversation):
    @checkLocalProtocol
    def run():
        c : Conversation = super.c
        c.join('B1', 'alice')

        c.send('S', "GoT")
        c.recv('S')

        c.send('B2', 100)

        c.stop()

class B2(BaseConversation):
    @checkLocalProtocol
    def run():
        c : Conversation = super.c
        c.join('B2', 'bob')

        c.recv('S')
        c.recv('B1')
        c.send('S', "hello")

        c.stop()
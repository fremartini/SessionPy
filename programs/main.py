from channel import Channel, Branch
from sessiontype import *

ch = Channel[Offer[  Send[int, 'jump'],  Recv[str, Label['jump', Recv[bool, End]]]   ]]()
match ch.offer():
    case Branch.LEFT:
        ch.send(42)
        b = ch.recv()
        assert b == bool
    case Branch.RIGHT:
        s = ch.recv()
        b = ch.recv()

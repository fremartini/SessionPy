from channel import Channel, Branch
from sessiontype import *

ch = Channel[Send[int, Offer[  Send[str, Recv[str, End]],  Send[int, End]  ]]]()
ch.send(5)

match ch.offer():
    case Branch.LEFT:
        ch.send("hello!")
        msg = ch.recv()

    case Branch.RIGHT:
        ch.send(42)


from channel import Channel, Branch
from sessiontype import *

ch = Channel[Choose[Send[int, End], Offer[Recv[int, End], Recv[bool, Send[str, End]]]]]()

if 2 > 1:
    ch.choose(Branch.RIGHT)
    match ch.offer():
        case Branch.LEFT:
            i = ch.recv()
        case Branch.RIGHT:
            b = ch.recv()
            ch.send('oops')
else:
    ch.choose(Branch.LEFT)
    ch.send(42)
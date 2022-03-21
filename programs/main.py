from channel import Channel, Branch
from sessiontype import *

ch = Channel[Recv[int, Choose[   Send[str, End],   Choose[  Send[int, End],  Recv[int, End]]]]]()
n = ch.recv()

if 10 > 5:
    ch.choose(Branch.LEFT)
    ch.send("number was greater than 5")
else:
    ch.choose(Branch.RIGHT)
    if 1 + 3 > 4:
        ch.choose(Branch.LEFT)
        ch.send(1)
    else:
        ch.choose(Branch.RIGHT)
        ch.recv()

from channel import Channel, Branch
from sessiontype import *


ch = Channel[Choose[Send[str, Recv[int, End]], Recv[int, Send[bool, End]]]]()



if 2 < 4:
    ch.choose(Branch.LEFT)
    ch.send('s')
    i = ch.recv()
else:
    ch.choose(Branch.RIGHT)
    i = ch.recv()
    ch.send(2 == 2)
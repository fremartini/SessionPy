from channel import Channel, Branch
from sessiontype import *

ch = Channel[Choose[ Send[int, Label['inner', Recv[bool, 'jump']]], Label['jump', Recv[str, Send[bool, 'inner']]]] ]()
ch.choose(Branch.LEFT)
ch.send(42+3)
b = ch.recv()
s = ch.recv()
ch.send(2 < 3)
ch.recv()
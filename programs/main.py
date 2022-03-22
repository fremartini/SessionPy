from channel import Channel, Branch
from sessiontype import *

ch = Channel[Label['main', Send[int, Label['switch', Choose [ 'main',  Send[bool, Recv[bool, 'switch']]]]  ]]]()

while True:
    ch.send(42)
    while True:
        ch.choose(Branch.RIGHT)
        ch.send(True)
        b = ch.recv()
    ch.choose(Branch.LEFT)


from channel import Channel, Branch
from sessiontype import *

ch = Channel[Label['main', Send[int, Label['inner', Choose [ 'main',  Recv[bool, Send[str, 'inner'] ]]]]]]()

ch.send(42)
while True:
    while True:
        ch.choose(Branch.RIGHT)
        b = ch.recv()
        ch.send('hi')
    ch.choose(Branch.LEFT)
    ch.send(100)

        


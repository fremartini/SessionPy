from channel import *
ch = Channel[Label['main', Choose [Send[int, Recv[str, 'main'] ], Recv[bool, Send[float, 'main' ]]]]]()

while True:
    if 2 < 15:
        ch.choose(Branch.RIGHT)
        b = ch.recv()
        ch.send(3.14)
    else:
        ch.choose(Branch.LEFT)
        ch.send(12)
        ch.recv()



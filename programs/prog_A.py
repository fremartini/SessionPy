from context import *

ch = Channel(Offer[Send[int, End], Recv[int, End]], ('localhost', 5006), ('localhost', 5011))

match ch.offer():
    case Branch.LEFT:
        ch.send(5)
    case Branch.RIGHT:
        a = ch.recv()
        print(a)
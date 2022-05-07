from sessiontype import *
from channel import Channel

routing = {'self': ('localhost', 50_000), 'Alice': ('localhost', 50_505)}

Neg = Recv[int, 'Alice', Send[int, 'Alice', End]]
Add = Recv[int, 'Alice', Recv[int, 'Alice', Send[int, 'Alice', End]]]
ch = Channel(Offer ['Alice', {"neg": Neg, "add": Add}], routing, dynamic_check = False)


negate = lambda x: -x
add = lambda x: lambda y: x + y

def dynServer(c):
    match c.offer():
        case "neg": serveOp(1, negate, c)
        case "add": serveOp(2, add, c)

def serveOp(n, op, c):
    if n == 0:
        c.send(op)
    else:
        v = c.recv()
        serveOp(n-1, op(v), c)



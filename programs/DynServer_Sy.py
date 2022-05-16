from context import *

roles = {'self': ('localhost', 5000), 'Rob': ('localhost', 5005), }

ch = Channel(Offer['Rob', {"neg": Recv[int, 'Rob', Send[int, 'Rob', End]],
                           "add": Recv[int, 'Rob', Recv[int, 'Rob', Send[int, 'Rob', End]]]}], roles)

negate = lambda x: -x
add = lambda x: lambda y: x + y


def dynServer(c):
    match c.offer():
        case "neg":
            serveOp(1, negate, c)
        case "add":
            serveOp(2, add, c)


def serveOp(n, op, c):
    if n == 0:
        c.send(op)
    else:
        v = c.recv()
        serveOp(n - 1, op(v), c)


dynServer(ch)

from context import *

routing_table = {'self': ('localhost', 5000), 'Client': ('localhost', 5001)}

ep = Endpoint(Offer['Client', {'neg': Recv[int, 'Client', Send[int, 'Client', End]], 'add': Recv[int, 'Client', Recv[int, 'Client', Send[int, 'Client', End]]]}], routing_table, static_check=False)

negate = lambda x: -x
add = lambda x: lambda y: x + y


def dyn_server(c):
    match c.offer():
        case "neg":
            serve_op(1, negate, c)
        case "add":
            serve_op(2, add, c)


def serve_op(n, op, c):
    if n == 0:
        c.send(op)
    else:
        v = c.recv()
        serve_op(n - 1, op(v), c)


dyn_server(ep)
from sessiontype import *
from channel import Channel

routing = {'self': ('localhost', 50_000), 'Alice': ('localhost', 50_505)}

recv_int_loop = Recv[int, 'Alice', 'loop']
send_int_end = Send[int, 'Alice', End]
neg_typ = Label['loop', Choose['Alice', {'receiver': recv_int_loop, 'sender': send_int_end}]]
add_typ = Label['loop', Choose['Alice', {'receiver': recv_int_loop, 'sender': send_int_end}]]
ch = Channel(Offer ['Alice', {"neg": neg_typ, "add": add_typ}], routing)


negate = lambda x: -x
add = lambda x: lambda y: x + y

def dyn_server(c):
    match c.offer():
        case "neg": serve_op(1, negate, c)
        case "add": serve_op(2, add, c)

def serve_op(n, op, c):
    if n == 0:
        c.choose('sender')
        c.send(op)
    else:
        c.choose('receiver')
        v = c.recv()
        serve_op(n-1, op(v), c)

dyn_server(ch)



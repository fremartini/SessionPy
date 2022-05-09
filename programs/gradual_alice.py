from context import *

routing = {'self': ('localhost', 50_505), 'Bob': ('localhost', 50_000)}

Neg = Send[int, 'Bob', Recv[int, 'Bob', End]]
Add = Send[int, 'Bob', Send[int, 'Bob', Recv[int, 'Bob', End]]]
ch = Channel(Choose['Bob', {"neg": Neg, "add": Add}], routing)

negate = lambda x: -x
add = lambda x: lambda y: x + y


def do_negate(c):
    c.choose("neg")
    c.send(42)
    v = c.recv()
    print('received:', v)


def do_add(c):
    c.choose("add")
    c.send(42)
    c.send(42)
    v = c.recv()
    print('received', v)


do_add(ch)

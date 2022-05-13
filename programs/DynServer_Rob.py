from context import *

roles = {'Sy': ('localhost', 5000), 'self': ('localhost', 5005), }

ch = Channel(Choose['Sy', {"neg": Send[int, 'Sy', Recv[int, 'Sy', End]],
                           "add": Send[int, 'Sy', Send[int, 'Sy', Recv[int, 'Sy', End]]]}], roles)


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

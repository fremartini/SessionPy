from context import *

roles = {'Sy': ('localhost', 5000), 'self': ('localhost', 5005), }

session_typ = Choose['Sy', {"neg": Send[int, 'Sy', Recv[int, 'Sy', End]],
                           "add": Send[int, 'Sy', Send[int, 'Sy', Recv[int, 'Sy', End]]]}]
ch = Channel(Choose['Sy', {"neg": Send[int, 'Sy', Recv[int, 'Sy', End]],
                           "add": Send[int, 'Sy', Send[int, 'Sy', Recv[int, 'Sy', End]]]}], roles)


def do_negate(c: session_typ):
    c.choose("neg")
    c.send(42)
    v = c.recv()
    print('received:', v)


def do_add(c: Send[int, 'Sy', ...]):
    c.send(42)
    c.send(42)
    v = c.recv()
    print('received', v)

do_negate(ch)

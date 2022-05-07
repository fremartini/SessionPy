from sessiontype import *
from channel import Channel

routing = {'self': ('localhost', 50_505), 'Bob': ('localhost', 50_000)}

Neg = Send[int, 'Bob', Recv[int, 'Bob', End]]
Add = Send[int, 'Bob', Send[int, 'Bob', Recv[int, 'Bob', End]]]
ch = Channel(Choose ['Bob', {"neg": Neg, "add": Add}], routing)

negate = lambda x: -x
add = lambda x: lambda y: x + y

def do_negate(c):
    c.choose("neg")
    c.send(42)
    v = c.recv() 
    assert v == -42

def do_add(c):
    c.choose("add")
    c.send(42)
    c.send(42)
    v = c.recv() 
    assert v == 84

do_negate(ch)



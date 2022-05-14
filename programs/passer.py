from context import *

routing = {'self': ('localhost', 50_000), 'Alice': ('localhost', 50_505)}
ch = Channel(Recv[str, 'Alice', Send[int, 'Alice', Recv[bool, 'Alice', End]]], routing)

def f(c: Recv[str, 'Alice', Send[int, 'Alice', ...]]):
    c.recv()
    
f(ch)
ch.send(2)
ch.recv()
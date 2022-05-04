from context import *

ch = Channel(Recv[int, 'other', End], {'self': ('localhost', 5005), 'other': ('localhost', 5000)})

b = ch.recv()
print('received ', b)

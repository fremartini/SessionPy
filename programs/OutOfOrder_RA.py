from channel import Channel
from sessiontype import *

roles = {'self': ('localhost', 5000), 'RB': ('localhost', 5001), 'RC': ('localhost', 5002),}

ch = Channel(Recv[int, 'RB', Recv[int, 'RC', End]], roles, static_check=False)

a = ch.recv()
print(a)
b = ch.recv()
print(b)
ch.close()

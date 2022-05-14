from context import *

roles = {'self': ('localhost', 5000), 'c1': ('localhost', 5001), 'c2': ('localhost', 5002), 'c3': ('localhost', 5003), }

ch = Channel(
    Send[List, 'c1', Send[List, 'c2', Send[List, 'c3', Recv[int, 'c1', Recv[int, 'c2', Recv[int, 'c2', End]]]]]], roles)

ch.send([1, 2, 3])
ch.send([4, 5, 6])
ch.send([7, 8, 9])

r1 = ch.recv()
r2 = ch.recv()
r3 = ch.recv()

print(r1 + r2 + r3)

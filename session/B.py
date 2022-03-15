from channel import *
from sessiontype import *

ch = Channel[Recv[int, End]](('localhost', 50000))

a = ch.recv()
print('received', a)
ch.send("hello world")

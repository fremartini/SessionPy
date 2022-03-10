from channel import *
from sessiontype import *

ch = Channel[Recv[str, End]](('localhost', 50000))

a = ch.recv()
print('received ', a)
ch.send("hello world")

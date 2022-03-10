from channel import *
from sessiontype import *

ch = Channel[Send[str, End]](('localhost', 50000))

ch.send("hello world")
a = ch.recv()
print('received ', a)

from channel import *
from sessiontype import *

ch = Channel[Send[int, End]](('localhost', 50000))

ch.send(13)
a = ch.recv()
print('received', a)

import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from src.channel import *
from src.sessiontype import *

ch = Channel[Recv[int, End]](('localhost', 50000))

a = ch.recv()
print('received', a)
ch.send("hello world")

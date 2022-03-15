import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from src.channel import *
from src.sessiontype import *

ch = Channel[Send[int, End]](('localhost', 50000))

ch.send(13)
a = ch.recv()
print('received', a)

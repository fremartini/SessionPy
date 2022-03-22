from channel import Channel, Branch
from sessiontype import *

RecvStringEnd = Recv[str, End]
DEBUG.print_envs()
my_chan = Channel[Send[int, RecvStringEnd]]()
        


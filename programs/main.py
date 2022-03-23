from channel import Channel, Branch
from sessiontype import *

my_chan = Channel[Label['rec', Send[int, 'rec']]]()



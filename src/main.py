from channel import Channel, Branch
from sessiontype import *
from typing import List, Tuple, Dict


ch = Channel(Send[int,End])
ch.send(int(42.42))

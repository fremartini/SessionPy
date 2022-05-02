from channel import Channel, Branch
from sessiontype import *
from typing import List, Tuple, Dict


ch = Channel(Recv[int, End], ("localhost", 50_005), ("localhost", 50_000))
i = ch.recv()
print("main1: received", i)





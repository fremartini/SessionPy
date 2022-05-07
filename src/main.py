from sessiontype import *
from channel import Channel
from typing import *

LeftOffer = Send[Tuple[str, int], "Marco", End]
RightOffer = Recv[str, "Frank", Send[Dict[float, str], "Marco", End]]
ch = Channel(Send[List[int], "Bobby", Choose["Marco", { 'a': LeftOffer, 'b': RightOffer}]], {'self': ('localhost', 50000)})
ch.send([1, 2])
ch.choose('a')
ch.send(("hi",2))

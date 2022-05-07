from sessiontype import *
from channel import Channel
from typing import *

LeftOffer = Send[Tuple[str, int], "Charlie", End]
RightOffer = Recv[str, "Alice", Send[Dict[float, str], "Bobby", End]]
ch = Channel(Send[List[int], "Bobby", Offer["Bobby", {'option1': LeftOffer, 'option2': RightOffer, 'option3': End}]], {'self': ('localhost', 4200)})
ch.send([1, 2])
match ch.offer():
    case "option1":
        ch.send(('cool', 42))
    case "option2":
        s = ch.recv()
        ch.send({3.14: 'pi'})
    case "option3":
        2+2
    

from channel import Channel, Branch
from sessiontype import *

def ok():
    LeftOffer = Send[Tuple[str, int], 'repeat']
    RightOffer = Recv[str, Send[Dict[float, str], 'repeat']]
    ch = Channel[Send[List[int], Label['repeat', Offer[LeftOffer, RightOffer]]]]()
    ch.send([1, 2])
    while 2 + 2 == 4:
        match ch.offer():
            case Branch.LEFT:
                ch.send(('cool', 42))
            case Branch.RIGHT:
                s = ch.recv()
                ch.send({3.14: 'pi'})

# Alice POV
from sessiontype import *
from channel import Channel

routing = {
    'self': ('localhost', 50_000), 
    'Bob': ('localhost', 50_505)
}

ch = Channel(Offer['Bob', Send[int, 'Bob', End], Recv[str, 'Bob', End]], routing, static_check=False)

match ch.offer():
    case Branch.LEFT: 
        ch.send(42)
    case Branch.RIGHT:
        s = ch.recv()
        print(f'received {s} from Bob')


from context import *
from diamond_util import *

ch = Channel[Recv[str, Send[Catalogue, Offer[Recv[str, Send[str, End]], Recv[DiamondColour, Send[str, End]]]]]](
    ("localhost", 5005), ("localhost", 5000))
req = ch.recv()
print('Received request from seller:', req)
catalogue = {
    DiamondColour.RED: 1_000_000,
    DiamondColour.BLUE: 500_000,
    DiamondColour.YELLOW: 50_000,
}
ch.send(catalogue)
match ch.offer():
    case Branch.LEFT:
        ch.send("It is okay, my diamonds are very expensive")
    case Branch.RIGHT:
        colour = ch.recv()
        ch.send(
            f'Thanks for purchasing a {colour} diamond, you spent ${catalogue[colour]}')


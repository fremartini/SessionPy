from context import *
from DiamondTransaction_util import *

roles = {'Buyer': ('localhost', 5000), 'self': ('localhost', 5005), }

ch = Channel(Recv[str, 'Buyer', Send[dict, 'Buyer', Choose[
    'Buyer', {"purchase": Recv[DiamondColor, 'Buyer', Send[str, 'Buyer', End]], "reject": Send[str, 'Buyer', End]}]]],
             roles)

req = ch.recv()
print('Received request from seller:', req)
catalogue = {
    DiamondColor.RED: 1_000_000,
    DiamondColor.BLUE: 500_000,
    DiamondColor.YELLOW: 50_000,
}
ch.send(catalogue)
match ch.offer():
    case 'reject':
        ch.send("It is okay, my diamonds are very expensive")
    case 'purchase':
        colour = ch.recv()
        ch.send(
            f'Thanks for purchasing a {colour} diamond, you spent ${catalogue[colour]}')

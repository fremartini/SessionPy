from context import *

Price = int
Catalogue = dict[int, Price]
DiamondColor = int
red = 0
blue = 1
yellow = 2

routing_table = {'Buyer': ('localhost', 5000), 'self': ('localhost', 5005), }

ch = Endpoint(Recv[str, 'Buyer', Send[dict, 'Buyer', Offer['Buyer', {"purchase": Recv[DiamondColor, 'Buyer', Send[str, 'Buyer', End]], "reject": Send[str, 'Buyer', End]}]]], routing_table)

req = ch.recv()
print('Received request from seller:', req)
catalogue = {
    red: 1_000_000,
    blue: 500_000,
    yellow: 50_000,
}
ch.send(catalogue)
match ch.offer():
    case 'reject':
        ch.send("It is okay, my diamonds are very expensive")
    case 'purchase':
        colour = ch.recv()
        ch.send(
            f'Thanks for purchasing a {colour} diamond, you spent ${catalogue[colour]}')

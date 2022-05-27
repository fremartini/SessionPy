from context import *

Price = int
Catalogue = dict[int, Price]
DiamondColor = int
red = 0
blue = 1
yellow = 2

routing_table = {'Buyer': ('localhost', 5000), 'self': ('localhost', 5005), }

ep = Endpoint(Recv[str, 'Buyer', Send[dict[int, int], 'Buyer', Offer['Buyer', {"purchase": Recv[DiamondColor, 'Buyer', Send[str, 'Buyer', End]], "reject": Send[str, 'Buyer', End]}]]], routing_table)

req = ep.recv()
print('Received request from seller:', req)
catalogue = {
    red: 1_000_000,
    blue: 500_000,
    yellow: 50_000,
}
ep.send(catalogue)
match ep.offer():
    case 'reject':
        ep.send("It is okay, my diamonds are very expensive")
    case 'purchase':
        colour = ep.recv()
        ep.send(
            f'Thanks for purchasing a {colour} diamond, you spent ${catalogue[colour]}')

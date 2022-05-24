from context import *

Price = int
Catalogue = dict[int, Price]
DiamondColor = int
red = 0
blue = 1
yellow = 2

routing_table = {'self': ('localhost', 5000), 'Seller': ('localhost', 5005), }

ch = Endpoint(Send[str, 'Seller', Recv[dict, 'Seller', Choose['Seller', {"purchase": Send[DiamondColor, 'Seller', Recv[str, 'Seller', End]], "reject": Recv[str, 'Seller', End]}]]], routing_table)

my_balance = 500_000  # USD

ch.send("Hi! I'd like to purchase a diamond")
catalogue : Catalogue = ch.recv()
best_diamond = None

for colour in catalogue:
    price = catalogue[colour]
    if (best_diamond and price > catalogue[best_diamond]
            or not best_diamond and price <= my_balance):
        best_diamond = colour

if best_diamond:
    ch.choose('purchase')
    ch.send(best_diamond)
    receipt: str = ch.recv()
    print('Receipt from seller:', receipt)
    my_balance -= catalogue[best_diamond]
else:
    ch.choose('reject')
    response = ch.recv()
    print('Response from seller:', response)

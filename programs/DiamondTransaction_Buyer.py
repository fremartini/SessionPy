from context import *
from DiamondTransaction_util import *

roles = {'self': ('localhost', 5000), 'Seller': ('localhost', 5005), }

ch = Channel(Send[str, 'Seller', Recv[dict, 'Seller', Offer[
    'Seller', {"purchase": Send[DiamondColor, 'Seller', Recv[str, 'Seller', End]],
               "reject": Recv[str, 'Seller', End]}]]], roles)

my_balance = 500_000  # USD

ch.send("Hi! I'd like to purchase a diamond")
catalogue: Catalogue = ch.recv()
best_diamond: DiamondColor | None = None

for colour in catalogue:
    price = catalogue[colour]
    if (best_diamond and price > catalogue.get(best_diamond)
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

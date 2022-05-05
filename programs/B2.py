from context import *

roles = {'B1': ('localhost', 5000), 'self': ('localhost', 5001), 'Seller': ('localhost', 5002),}

ch = Channel(Recv[str, 'Seller', Recv[float, 'B1', Offer['Seller', Send[str, 'Seller', End], End]]], roles)

quote = ch.recv()
print(quote)

amount = ch.recv()
print(amount)

ch.choose(Branch.LEFT)
ch.send('Address')

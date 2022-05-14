from context import *

roles = {'B1': ('localhost', 5000), 'self': ('localhost', 5001), 'Seller': ('localhost', 5002), }

ch = Channel(
    Recv[float, 'Seller', Recv[float, 'B1', Offer['Seller', {"buy": Send[str, 'Seller', End], "reject": End}]]], roles)

quote = ch.recv()
print(quote)

amount = ch.recv()
print(amount)

ch.choose('buy')
ch.send('Address')

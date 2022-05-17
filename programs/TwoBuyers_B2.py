from context import *

roles = {'B1': ('localhost', 5000), 'self': ('localhost', 5001), 'Seller': ('localhost', 5002), }

ch = Channel(Recv[float, 'Seller', Recv[float, 'B1', Offer['Seller', {"buy": Send[str, 'Seller', End], "reject": End}]]], roles)

quote = ch.recv()
contrib = ch.recv()

if quote - contrib <= 99:
    ch.choose('buy')
    ch.send('here is my address')
else:
    ch.choose('reject')
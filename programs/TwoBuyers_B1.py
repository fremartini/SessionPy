from context import *

roles = {'self': ('localhost', 5000), 'B2': ('localhost', 5001), 'Seller': ('localhost', 5002),}

ch = Channel(Send[str, 'Seller', Recv[float, 'Seller', Send[float, 'B2', End]]], roles)

ch.send('War and Peace')
quote = ch.recv()
ch.send(quote/2)

from context import *

roles = {'self': ('localhost', 5000), 'B2': ('localhost', 5001), 'Seller': ('localhost', 5002),}

ch = Channel(Send[str, 'Seller', Recv[str, 'Seller', Send[float, 'B2', End]]], roles)

ch.send('book')
quote = ch.recv()
print(quote)

ch.send(50.2)
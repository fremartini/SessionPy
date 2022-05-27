from context import *

routing_table = {'self': ('localhost', 5000), 'B2': ('localhost', 5001), 'Seller': ('localhost', 5002),}

ep = Endpoint(Send[str, 'Seller', Recv[float, 'Seller', Send[float, 'B2', End]]], routing_table)

ep.send('War and Peace')
quote = ep.recv()
ep.send(quote / 2)

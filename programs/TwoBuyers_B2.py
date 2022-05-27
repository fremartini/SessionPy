from context import *

routing_table = {'B1': ('localhost', 5000), 'self': ('localhost', 5001), 'Seller': ('localhost', 5002),}

ep = Endpoint(Recv[float, 'Seller', Recv[float, 'B1', Choose['Seller', {"buy": Send[str, 'Seller', End], "reject": End}]]], routing_table)

quote = ep.recv()
contrib = ep.recv()

if quote - contrib <= 99:
    ep.choose('buy')
    ep.send('here is my address')
else:
    ep.choose('reject')

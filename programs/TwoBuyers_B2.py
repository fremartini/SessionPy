from context import *

routing_table = {'B1': ('localhost', 5000), 'self': ('localhost', 5001), 'Seller': ('localhost', 5002),}

ch = Channel(Recv[float, 'Seller', Recv[float, 'B1', Choose['Seller', {"buy": Send[str, 'Seller', End], "reject": End}]]], routing_table)

quote = ch.recv()
contrib = ch.recv()

if quote - contrib <= 99:
    ch.choose('buy')
    ch.send('here is my address')
else:
    ch.choose('reject')

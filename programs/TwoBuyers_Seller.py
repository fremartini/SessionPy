from context import *

routing_table = {'B1': ('localhost', 5000), 'B2': ('localhost', 5001), 'self': ('localhost', 5002),}

ch = Endpoint(Recv[str, 'B1', Send[float, 'B1', Send[float, 'B2', Offer['B2', {"buy": Recv[str, 'B2', End], "reject": End}]]]], routing_table)

title = ch.recv()

quote = 120.0
ch.send(quote)
ch.send(quote)

match ch.offer():
    case 'buy':
        address = ch.recv()
    case 'reject':
        ...


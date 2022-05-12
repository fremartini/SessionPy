from context import *

roles = {'B1': ('localhost', 5000), 'B2': ('localhost', 5001), 'self': ('localhost', 5002),}

ch = Channel(Recv[str, 'B1', Send[float, 'B1', Send[float, 'B2', Choose['B2', {"buy": Recv[str, 'B2', End], "reject": End}]]]], roles, static_check=False)

title = ch.recv()
print(title)
quote = 1.2
ch.send(quote)
ch.send(quote)

match ch.offer():
    case 'buy':
        address = ch.recv()
        print(address)
    case 'reject':
        ...

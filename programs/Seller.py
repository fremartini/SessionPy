from context import *

roles = {'B1': ('localhost', 5000), 'B2': ('localhost', 5001), 'self': ('localhost', 5002),}

ch = Channel(Recv[str, 'B1', Send[str, 'B1', Send[str, 'B2', Choose['B2', Recv[str, 'B2', End], End]]]], roles)

title = ch.recv()
print(title)
quote = 'quote'
ch.send(quote)
ch.send(quote)

match ch.offer():
    case Branch.LEFT:
        address = ch.recv()
        print(address)
    case Branch.RIGHT:
        ...

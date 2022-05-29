from context import *

routing_table = {'self': ('localhost', 5000), 'Client': ('localhost', 5001)}

ep = Endpoint(Offer['Client', {"add": Recv[int, 'Client', Recv[int, 'Client', Send[int, 'Client', End]]], "neg": Recv[int, 'Client', Send[int, 'Client', End]], "mul": Recv[int, 'Client', Recv[int, 'Client', Send[int, 'Client', End]]]}], routing_table)

match ep.offer():
    case 'add':
        ep.send(ep.recv() + ep.recv())
    case 'neg':
        ep.send(ep.recv() * -1)
    case 'mul':
        ep.send(ep.recv() * ep.recv())

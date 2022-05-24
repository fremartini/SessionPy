from context import *

routing_table = {'self': ('localhost', 5000), 'Client': ('localhost', 5001)}

ch = Channel(Offer['Client', {"add": Recv[int, 'Client', Recv[int, 'Client', Send[int, 'Client', End]]], "neg": Recv[int, 'Client', Send[int, 'Client', End]], "mul": Recv[int, 'Client', Recv[int, 'Client', Send[int, 'Client', End]]]}], routing_table)

match ch.offer():
    case 'add':
        ch.send(ch.recv() + ch.recv())
    case 'neg':
        ch.send(ch.recv() * -1)
    case 'mul':
        ch.send(ch.recv() * ch.recv())

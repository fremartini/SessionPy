from context import *

routing_table = {'self': ('localhost', 0), 'Client': ('localhost', 0)}

ch = Channel(Offer['Client', {"add": Recv[int, 'Client', Recv[int, 'Client', Send[int, 'Client', End]]], "neg": Recv[int, 'Client', Send[int, 'Client', End]], "mul": Recv[int, 'Client', Recv[int, 'Client', Send[int, 'Client', End]]]}], routing_table)

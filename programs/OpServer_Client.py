from context import *

routing_table = {'Server': ('localhost', 0), 'self': ('localhost', 0)}

ch = Channel(Choose['Server', {"add": Send[int, 'Server', Send[int, 'Server', Recv[int, 'Server', End]]], "neg": Send[int, 'Server', Recv[int, 'Server', End]], "mul": Send[int, 'Server', Send[int, 'Server', Recv[int, 'Server', End]]]}], routing_table)

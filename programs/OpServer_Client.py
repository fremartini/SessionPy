from context import *

routing_table = {'Server': ('localhost', 5000), 'self': ('localhost', 5001)}

ch = Endpoint(Choose['Server', {"add": Send[int, 'Server', Send[int, 'Server', Recv[int, 'Server', End]]], "neg": Send[int, 'Server', Recv[int, 'Server', End]], "mul": Send[int, 'Server', Send[int, 'Server', Recv[int, 'Server', End]]]}], routing_table)

ch.choose('mul')
ch.send(5)
ch.send(7)
print(ch.recv())

from context import *

routing_table = {'Server': ('localhost', 5000), 'self': ('localhost', 5001)}

ep = Endpoint(Choose['Server', {"add": Send[int, 'Server', Send[int, 'Server', Recv[int, 'Server', End]]], "neg": Send[int, 'Server', Recv[int, 'Server', End]], "mul": Send[int, 'Server', Send[int, 'Server', Recv[int, 'Server', End]]]}], routing_table)

ep.choose('mul')
ep.send(5)
ep.send(7)
print(ep.recv())

from context import *

routing_table = {'Distributor': ('localhost', 5000), 'c1': ('localhost', 5001), 'self': ('localhost', 5002),
                 'c3': ('localhost', 5003)}

ch = Channel(Recv[List[str], 'Distributor', Send[Dict[str, int], 'Distributor', End]], routing_table)

words: List[str] = ch.recv()

mapping: Dict[str, int] = {}

for w in words:
    mapping[w] = mapping.get(w, 0) + 1

ch.send(mapping)

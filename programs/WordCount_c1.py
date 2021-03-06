from context import *

routing_table = {'Distributor': ('localhost', 5000), 'self': ('localhost', 5001), 'c2': ('localhost', 5002),
                 'c3': ('localhost', 5003)}

ep = Endpoint(Recv[list[str], 'Distributor', Send[dict[str, int], 'Distributor', End]], routing_table, static_check=False)

words: list[str] = ep.recv()

mapping: dict[str, int] = {}

for w in words:
    mapping[w] = mapping.get(w, 0) + 1

ep.send(mapping)

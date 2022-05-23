from context import *

routing_table = {'self': ('localhost', 5000), 'c1': ('localhost', 5001), 'c2': ('localhost', 5002),
                 'c3': ('localhost', 5003)}

ch = Channel(Send[list[str], 'c1',
                  Send[list[str], 'c2',
                       Send[list[str], 'c3',
                            Recv[dict[str, int], 'c1',
                                 Recv[dict[str, int], 'c2',
                                      Recv[dict[str, int], 'c3', End]]]]]], routing_table, static_check=False)

ch.send(['Deer', 'Bear', 'River', 'River', 'Bear'])
ch.send(['Car', 'Car', 'River', 'River', 'River'])
ch.send(['Deer', 'Car', 'Bear', 'Car'])

r1: dict[str, int] = ch.recv()
r2: dict[str, int] = ch.recv()
r3: dict[str, int] = ch.recv()

for k, v in r2.items():
    r1[k] = r1.get(k, 0) + v

for k, v in r3.items():
    r1[k] = r1.get(k, 0) + v

print(r1)

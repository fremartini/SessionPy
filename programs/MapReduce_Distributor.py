from context import *

routing_table = {'self': ('localhost', 5000), 'c1': ('localhost', 5001), 'c2': ('localhost', 5002),
                 'c3': ('localhost', 5003)}

ch = Channel(Send[list[str], 'c1',
                  Send[list[str], 'c2',
                       Send[list[str], 'c3',
                            Recv[dict[str, int], 'c1',
                                 Recv[dict[str, int], 'c2',
                                      Recv[dict[str, int], 'c3', End]]]]]], routing_table)

ch.send(['Deer', 'Bear', 'River'])
ch.send(['Car', 'Car', 'River'])
ch.send(['Deer', 'Car', 'Bear'])

r1 = ch.recv()
r2 = ch.recv()
r3 = ch.recv()

print(r1 | r2 | r3)

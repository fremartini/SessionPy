from context import *

routing_table = {'self': ('localhost', 5000), 'RB': ('localhost', 5001), 'RC': ('localhost', 5002),}

ch = Endpoint(Label["LOOP", Recv[int, 'RB', Recv[int, 'RC', "LOOP"]]], routing_table)

while True:
    a = ch.recv()
    print(a)
    b = ch.recv()
    print(b)

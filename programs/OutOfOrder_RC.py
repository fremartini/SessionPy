from context import *

routing_table = {'RA': ('localhost', 5000), 'RB': ('localhost', 5001), 'self': ('localhost', 5002),}

ep = Endpoint(Label["LOOP", Send[int, 'RA', "LOOP"]], routing_table)

while True:
    ep.send(1)
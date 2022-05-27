from context import *

routing_table = {'RA': ('localhost', 5000), 'self': ('localhost', 5001), 'RC': ('localhost', 5002),}

ep = Endpoint(Label["LOOP", Send[int, 'RA', "LOOP"]], routing_table)

while True:
    ep.send(42)

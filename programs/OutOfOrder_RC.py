from context import *

roles = {'RA': ('localhost', 5000), 'RB': ('localhost', 5001), 'self': ('localhost', 5002),}

ch = Channel(Label["LOOP", Send[int, 'RA', "LOOP"]], roles)

while True:
    ch.send(1)
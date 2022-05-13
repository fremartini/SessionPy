from context import *

roles = {'RA': ('localhost', 5000), 'self': ('localhost', 5001), 'RC': ('localhost', 5002),}

ch = Channel(Label["LOOP", Send[int, 'RA', "LOOP"]], roles)

while True:
    ch.send(42)

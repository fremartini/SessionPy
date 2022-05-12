from context import *

roles = {'RA': ('localhost', 5000), 'RB': ('localhost', 5001), 'self': ('localhost', 5002),}

ch = Channel(Send[int, 'RA', End], roles)

ch.send(1)
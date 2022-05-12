from channel import Channel
from sessiontype import *

roles = {'RA': ('localhost', 5000), 'RB': ('localhost', 5001), 'self': ('localhost', 5002),}

ch = Channel(Send[int, 'RA', End], roles, static_check=False)

ch.send(1)
ch.close()

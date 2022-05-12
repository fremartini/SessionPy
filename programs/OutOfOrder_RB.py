from context import *

roles = {'RA': ('localhost', 5000), 'self': ('localhost', 5001), 'RC': ('localhost', 5002),}

ch = Channel(Send[int, 'RA', End], roles, static_check=False)

ch.send(42)
ch.close()

from context import *

ch = Channel(Send[int, 'other', End], {'self': ('localhost', 5000), 'other': ('localhost', 5005)})

ch.send(5)
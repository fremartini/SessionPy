from context import *
ch = Channel(Label['looper', Send[int, "Alice", 'looper']], {'self': ()})

def f(c):
    c.send(42)

f(ch)
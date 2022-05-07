from channel import Channel
from check import typecheck_file
from sessiontype import *
#ch = Channel(Send[int, "Alice", Recv[str, "Bob", End]], {'self': ("localhost", 50000)})

ch = Channel(Send[int, "self", Send[bool, "self", End]], {'self': ("localhost", 50_000)})
x = lambda y: lambda z: ch.send(y+z)
xp = x(3)
xpp = xp(4)
xp(True)
#ch.recv("hi")

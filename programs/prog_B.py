from context import *

ch = Channel(Choose[Recv[int, End], Send[int, End]], ('localhost', 5011), ('localhost', 5006))

ch.choose(Branch.LEFT)
b = ch.recv()
print('received ', b)

from context import *

ch = Channel[Choose[Send[str, End], Send[int, End]]](('localhost', 5011), ('localhost', 5006))

a = ch.recv()
print('received ', a, type(a))

print('dict? ', ch.recv())
print('int ', ch.recv())

for i in range(20):
    print('recv ', ch.recv())

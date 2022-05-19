from context import *

routing_table = {'self': ('localhost', 50_000), 'Bob': ('localhost', 50_005),}

ch = Channel(Send[str, 'Bob', Recv[str, 'Bob', Label["TALK", Choose['Bob', {"talk": Recv[str, 'Bob', Send[str, 'Bob', "TALK"]], "stop": Send[str, 'Bob', End]}]]]], routing_table)

ch.send("hello")
s = ch.recv()

print('entering loop...')
for i in range(2):
    print(f'loop #{i}')
    ch.choose("talk")
    s = ch.recv()
    ch.send(s)
print('...exited loop')

ch.choose("stop")
ch.send("bye")
print('done!')

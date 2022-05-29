from context import *

routing_table = {'self': ('localhost', 50_000), 'Bob': ('localhost', 50_005),}

ep = Endpoint(Send[str, 'Bob', Recv[str, 'Bob', Label["TALK", Choose['Bob', {"talk": Recv[str, 'Bob', Send[str, 'Bob', "TALK"]], "stop": Send[str, 'Bob', End]}]]]], routing_table)

ep.send("hello")
s = ep.recv()

print('entering loop...')
for i in range(2):
    print(f'loop #{i}')
    ep.choose("talk")
    s = ep.recv()
    ep.send(s)
print('...exited loop')

ep.choose("stop")
ep.send("bye")
print('done!')

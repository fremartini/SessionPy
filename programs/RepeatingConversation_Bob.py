from context import *

roles = {'Alice': ('localhost', 5000), 'self': ('localhost', 5001),}

ch = Channel(Recv[str, 'Alice', Send[str, 'Alice', Label["TALK", Choose['Alice', {"talk": Send[str, 'Alice', Recv[str, 'Alice', "TALK"]], "stop": Recv[str, 'Alice', End]}]]]], roles, static_check=False)

print(ch.recv())
ch.send('Hello Alice!')

i = 0
while True:
    i = i + 1

    if i < 10:
        ch.choose('talk')
        ch.send('lets talk a bit more')
        print(ch.recv())
    else:
        ch.choose('stop')
        print(ch.recv())
        break

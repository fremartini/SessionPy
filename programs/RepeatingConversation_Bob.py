from context import *

roles = {'Alice': ('localhost', 5000), 'self': ('localhost', 5001), }

TheChoice = Choose['Alice', {"talk": Send[str, 'Alice', Recv[str, 'Alice', "loopy"]], "stop": Recv[str, 'Alice', 'loopy']}]
ch = Channel(Recv[str, 'Alice', Send[str, 'Alice', Label['loopy', Offer['Alice', {'loop': TheChoice, 'terminate': End}]]]], roles)

print(ch.recv())
ch.send('Hello Alice!')

i = 0
while True:
    i = i + 1

    match ch.offer():
        case 'loop':
            if i < 10:
                ch.choose('talk')
                ch.send('lets talk a bit more')
                print(ch.recv())
            else:
                ch.choose('stop')
                print(ch.recv())
                break
        case 'terminate':
            break



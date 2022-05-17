from context import *

roles = {'self': ('localhost', 5000), 'Bob': ('localhost', 5001),}
TheOffer = Offer['Bob', {"talk": Recv[str, 'Bob', Send[str, 'Bob', "loopy"]], "stop": Send[str, 'Bob', 'loopy']}]
ch = Channel(Send[str, 'Bob', Recv[str, 'Bob', Label['loopy', Choose['Bob', {'loop': TheOffer, 'terminate': End}]]]], roles)

ch.send('Hello Bob!')
print(ch.recv())

while True:
    ch.choose('loop')
    match ch.offer():
        case 'talk':
            print(ch.recv())
            ch.send('lets just pretend we are talking')
        case 'stop':
            ch.send('allright, talk to you later')
            break

ch.choose('terminate')
from context import *

roles = {'self': ('localhost', 5000), 'Bob': ('localhost', 5001), }

ch = Channel(Send[str, 'Bob', Recv[str, 'Bob', Label[
    "TALK", Offer['Bob', {"talk": Recv[str, 'Bob', Send[str, 'Bob', "TALK"]], "stop": Send[str, 'Bob', End]}]]]], roles)

ch.send('Hello Bob!')
print(ch.recv())

while True:
    match ch.offer():
        case 'talk':
            print(ch.recv())
            ch.send('lets just pretend we are talking')
        case 'stop':
            ch.send('allright, talk to you later')
            break

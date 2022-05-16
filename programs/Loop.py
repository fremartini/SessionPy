from context import *

routing = {'self': ('localhost', 50_000), 'Alice': ('localhost', 50_505)}
TheOffer = Offer['Alice', {'sendint_continue': Send[int, 'Alice', 'decision'], 'sendstr_stop': Send[str, 'Alice', 'decision']}]
ch = Channel(Label['decision', Choose['Alice', {'looping': TheOffer, 'rest': Send[int, 'Alice', End]} ]], routing)

while True:
    ch.choose('looping')
    match ch.offer():
        case 'sendint_continue':
            ch.send(42)
        case 'sendstr_stop':
            ch.send('hello')
            break
ch.choose('rest')
ch.send(42)



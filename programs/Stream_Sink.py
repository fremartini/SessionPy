from context import *

routing_table = {'Source': ('localhost', 5000), 'self': ('localhost', 5001)}

ch = Endpoint(Label["LOOP", Offer['Source', {"work": Recv[int, 'Source', "LOOP"], "stop": End}]], routing_table)

while True:
    match ch.offer():
        case 'work':
            print(ch.recv())
        case 'stop':
            break

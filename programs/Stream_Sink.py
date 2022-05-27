from context import *

routing_table = {'Source': ('localhost', 5000), 'self': ('localhost', 5001)}

ep = Endpoint(Label["LOOP", Offer['Source', {"work": Recv[int, 'Source', "LOOP"], "stop": End}]], routing_table)

while True:
    match ep.offer():
        case 'work':
            print(ep.recv())
        case 'stop':
            break

from context import *

routing_table = {'Alice': ('localhost', 50_000), 'self': ('localhost', 50_005),}

ch = Endpoint(Recv[str, 'Alice', Send[str, 'Alice', Label["TALK", Offer['Alice', {"talk": Send[str, 'Alice', Recv[str, 'Alice', "TALK"]], "stop": Recv[str, 'Alice', End]}]]]], routing_table)

s = ch.recv()
ch.send(s)

while True:
    match ch.offer():
        case "talk":
            ch.send(s)
            ch.recv()
        case "stop":
            ch.recv()
            break
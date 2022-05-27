from context import *

routing_table = {'Alice': ('localhost', 50_000), 'self': ('localhost', 50_005),}

ep = Endpoint(Recv[str, 'Alice', Send[str, 'Alice', Label["TALK", Offer['Alice', {"talk": Send[str, 'Alice', Recv[str, 'Alice', "TALK"]], "stop": Recv[str, 'Alice', End]}]]]], routing_table)

s = ep.recv()
ep.send(s)

while True:
    match ep.offer():
        case "talk":
            ep.send(s)
            ep.recv()
        case "stop":
            ep.recv()
            break
from context import *

routing_table = {'Server': ('localhost', 5000), 'self': ('localhost', 5001)}

session_type = Choose['Server', {'neg': Send[int, 'Server', Recv[int, 'Server', End]],
                                 'add': Send[int, 'Server', Send[int, 'Server', Recv[int, 'Server', End]]]}]
ep = Endpoint(session_type, routing_table)


def do_negate(c: session_type):
    c.choose("neg")
    c.send(42)
    print(c.recv())


def do_add(c: Send[int, 'Server', ...]):
    c.send(42)
    c.send(42)
    print(c.recv())


do_negate(ep)

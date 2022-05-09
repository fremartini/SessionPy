# Bob POV
from sessiontype import *
from channel import Channel

routing = {
    'self': ('localhost', 50_505), 
    'Alice': ('localhost', 50_000)
}

ch = Channel(Choose['Alice', Recv[int, 'Alice', End], Send[str, 'Alice', End]], routing, static_check=False)


def do_left(c):
    i = c.recv()
    print(f'received {i} from Alice')

def do_right(c):
    c.send("hello alice u wanker")

do_left(ch)


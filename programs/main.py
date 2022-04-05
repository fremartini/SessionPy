from channel import Channel, Branch
from sessiontype import *

chan = Channel[Send[int, Send[int, End]]]()
chan1 = Channel[Recv[str, Recv[str, End]]]()

def f(ch, ch1) -> str:
    ch.send(42)
    s = ch1.recv()
    return s

x = f(chan, chan1)
y = f(chan, chan1)



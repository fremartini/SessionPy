from channel import Channel, Branch
from sessiontype import *


def ok():
    def f(ch, ch1) -> str:
        ch.send(42)
        s = ch1.recv()
        ch.send(100)
        ch1.send(1239)
        return s
    f(Channel[Send[int, Send[int, End]]](), Channel[Recv[str, Send[int, End]]]())
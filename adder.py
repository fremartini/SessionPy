from channel import Branch, Channel
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = Channel[Recv[int, Recv[int, Send[int, End]]]]()
    x = ch.recv()
    y = ch.recv()
    res = 1+2
    ch.send(res)
    print('sent', 42)  # we expect this!

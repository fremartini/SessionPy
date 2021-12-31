from typechecking import verify_channels
from channel import *

@verify_channels
def main():
    ch = Channel[Recv[int, Recv[int, Send[int, End]]]]()
    x  = ch.recv()
    y  = ch.recv()
    res : int = x+y
    ch.send(res)
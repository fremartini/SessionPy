from typechecking import verify_channels
from channel import *

@verify_channels
def main():
    ch = Channel[Recv[int, Send[int, End]]]()
    x = ch.recv()
    ch.send(x)
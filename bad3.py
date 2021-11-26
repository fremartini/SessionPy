from channel import *
from sessiontype import *
from ast_playground import verify_channels

@verify_channels
def main():
    ch = Channel[Send[int, Recv[bool, End]]]()
    ch1 = Channel[Recv[str, Send[int, End]]]()
    v = ch.recv()
    ch.send(True)
    print('received value', v) # this should NOT happen - wrong type!
    print('sent value', True)  


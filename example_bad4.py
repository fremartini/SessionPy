from typechecking import verify_channels
from channel import *
from sessiontype import *

def f(ch: Channel):
    b = ch.recv()
    print('received value', b) # should happen; at this point we receive
    return b

@verify_channels
def main():
    ch = QChannel[Send[int, Recv[bool, Send[str, End]]]]()
    ch.send(42) 
    print('sent value', True)  # okay so far
    f(ch)
    s = ch.recv()
    print('received', s) # should NOT happen; at this point we should send

if __name__ == '__main__':
    main()
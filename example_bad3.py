from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = Channel[Send[int, Recv[bool, End]]]()
    ch1 = Channel[Recv[str, Send[int, End]]]()
    ch.send(True)
    v = ch1.recv()
    print('received value', v) # this should NOT happen - wrong type!
    print('sent value', True)  

if __name__ == '__main__':
    main()
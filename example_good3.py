from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = QChannel[Recv[int, Send[bool, End]]]()
    v = ch.recv()
    ch.send(True)
    print('received value', v) # this should happen!
    print('sent value', True)  

if __name__ == '__main__':
    main()
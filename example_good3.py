from channel import *
from sessiontype import *
from ast_playground import verify_channels

@verify_channels
def main():
    ch = Channel[Recv[int, Send[bool, End]]]()
    v = ch.recv()
    a = ch.send(True)
    print('received value', v) # this should happen!
    print('sent value', True)  

if __name__ == '__main__':
    main()

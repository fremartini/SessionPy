from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = Channel[Recv[int, End]]()
    v = ch.recv()
    print('received value', v) # this should happen!

if __name__ == '__main__':
    main()

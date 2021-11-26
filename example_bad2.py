from channel import *
from sessiontype import *
from ast_playground import verify_channels

@verify_channels
def main():
    ch = Channel[Recv[int, End]]()
    a = ch.send(42)
    print('sent value', 42) # should never happen

if __name__ == '__main__':
    main()
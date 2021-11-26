from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = QChannel[Recv[int, End]]()
    ch.send(42)
    print('sent value', 42) # should never happen

if __name__ == '__main__':
    main()
from channel import *
from sessiontype import *
from typechecking import verify_channels


@verify_channels
def main():
    ch = Channel[Recv[int, End]]()
    ch.send(2)


if __name__ == '__main__':
    main()

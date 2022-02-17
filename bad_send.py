from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = Channel[Send[int, Send[Channel[Recv[str, End]], End]]]()
    ch1 = Channel[Recv[str, End]]()
    ch.send(42)
    ch.send(ch1)

if __name__ == '__main__':
    main()

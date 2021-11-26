from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    c = QChannel[Send[int, Send[str, Recv[int, Recv[str, End]]]]]()
    c.send(1)
    c.send("hi")

    c.recv()
    c.recv()

if __name__ == '__main__':
    main()
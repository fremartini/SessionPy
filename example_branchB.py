from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = Channel[Recv[int, Choose[Send[str, End], Recv[int, End]]]]
    n = ch.recv()
    if n > 5:
        ch.choose(Branch.LEFT)
        print("B: left: sending string")
        ch.send("number was greater than 5")
    else:
        ch.choose(Branch.RIGHT)
        print("B: right: receiving integer")
        i = ch.recv()
        print(i)

if __name__ == '__main__':
    main()
from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = Channel[Send[int, Branch[Send[str, End], Recv[int, End]]]]
    ch.send(5)

    #offer = branch
    #select = 
    # client
    ch = ch.left()
    ch.send("hi!")

    # server code
    match ch.select():
        case Branch.Left: ... # this happens!
        case Branch.Right: ... # never happens!

if __name__ == '__main__':
    main()
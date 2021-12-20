from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = Channel[Send[int, Recv[bool, Send[str, End]]]]()
    ch.send(42) 
    print('sent value', True)  
    f(ch)
    ch.send("we're done here...") # ending the session

def f(ch: Channel):
    v = ch.recv()
    print('received value', 666) # this should happen! expecting a receive
    return v


if __name__ == '__main__':
    main()
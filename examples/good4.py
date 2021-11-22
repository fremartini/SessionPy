from channel import *
from sessiontype import *
from fromfile import check_file

def f(c: Channel):
    v = c.recv()
    print('received value', 666) # this should happen! expecting a receive
    return v

@check_file
def main():
    ch = Channel[Send[int, Recv[bool, Send[str, End]]]]()
    ch.send(42) 
    print('sent value', True)  
    f(ch)
    ch.send("we're done here...") # ending the session


if __name__ == '__main__':
    main()

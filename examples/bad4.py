from channel import *
from sessiontype import *
from fromfile import check_file

def f(c: Channel):
    b = c.recv()
    print('received value', b) # should happen; at this point we receive
    return b

@check_file
def main():
    ch = Channel[Send[int, Recv[bool, Send[str, End]]]]()
    ch.send(42) 
    print('sent value', True)  # okay so far
    f(ch)
    s = ch.recv()
    print('received', s) # should NOT happen; at this point we should send

if __name__ == '__main__':
    main()
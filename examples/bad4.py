from channel import *
from sessiontype import *
from fromfile import check_file

def f(c: Channel):
    c.send(666)
    print('sent value', 666) # should NOT happen; at this point we receive
    return True


def main():
    ch = Channel[Send[int, Recv[bool, ]]]()
    ch.send(42) 
    print('sent value', True)  # okay so far
    f(ch)

if __name__ == '__main__':
    main()

from channel import *
from sessiontype import *
from fromfile import check_file

@check_file
def main():
    ch = Channel[Send[int, Recv[bool, End]]]()
    v = ch.recv()
    ch.send(True)
    print('received value', v) # this should NOT happen - wrong type!
    print('sent value', True)  

if __name__ == '__main__':
    main()

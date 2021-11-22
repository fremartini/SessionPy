from channel import *
from sessiontype import *
from fromfile import check_file

def main():
    ch = Channel[Recv[int, Send[bool, End]]]()
    v = ch.recv()
    ch.send(True)
    print('received value', v) # this should happen!
    print('sent value', True)  

if __name__ == '__main__':
    main()

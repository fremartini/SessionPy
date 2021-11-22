from channel import *
from sessiontype import *
from fromfile import check_file

def main():
    ch = Channel[Send[int, End]]()
    v = ch.recv()
    print('received', v) # should never happen

if __name__ == '__main__':
    main()

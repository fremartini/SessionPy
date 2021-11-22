from channel import *
from sessiontype import *
from fromfile import check_file

def main():
    ch = Channel[Recv[int, End]]()
    ch.send(42)
    print('sent value', 42) # should never happen

if __name__ == '__main__':
    main()

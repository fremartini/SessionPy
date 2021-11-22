from channel import *
from sessiontype import *
from fromfile import check_file

@check_file
def main():
    ch = Channel[Recv[int, End]]()
    v = ch.recv()
    print('received value', v) # this should happen!

if __name__ == '__main__':
    main()

from channel import *
from sessiontype import *
from fromfile import check_file

def main():
    ch = Channel[Send[int, End]]()
    ch.send(42)
    print('sent', 42) # we expect this!

if __name__ == '__main__':
    main()

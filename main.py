from channel import *
from sessiontype import *

def main():
    ch = TCPChannel[Send[int, End]]()
    ch.send(42)

if __name__ == '__main__':
    main()
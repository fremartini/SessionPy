from channel import *
from sessiontype import *

def main():
    c  = Channel[Send[int, Send[str, End]]]()
    c.init()
    c.send(1)
    c.recv()

if __name__ == '__main__':
    main()
from channel import *
from sessiontype import *
from ast_playground import verify_channels

@verify_channels
def main():
    ch = Channel[Send[int, End]]()
    ch.send(42)
    print('sent', 42) # we expect this!

if __name__ == '__main__':
    main()

from channel import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = QChannel[Send[int, End]]()
    v = ch.recv()
    print('received', v) # should never happen

if __name__ == '__main__':
    main()
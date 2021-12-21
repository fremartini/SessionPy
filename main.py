from channel import *
from sessiontype import *
from typechecking import verify_channels


@verify_channels
def main():
    ch = Channel[Send[int, End]]()
    # ch.send(2)
    print('sent', 42)  # we expect this!


if __name__ == '__main__':
    main()

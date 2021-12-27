from channel import *
from sessiontype import *
from typechecking import verify_channels
from enum import Enum


class DiamondColour(Enum):
    RED = 0
    BLUE = 1
    YELLOW = 2


@verify_channels
def main():
    ch = Channel[Recv[str, Send[dict[DiamondColour, int],
                                Offer[Recv[str, Send[str, End]], Recv[DiamondColour, Send[str, End]]]]]]()
    req = ch.recv()
    print('Received request from seller:', req)
    catalogue = {
        DiamondColour.RED: 1_000_000,
        DiamondColour.BLUE: 500_000,
        DiamondColour.YELLOW: 50_000,
    }
    ch.send(catalogue)
    match ch.offer():
        case Branch.LEFT:
            ch.send("It is okay, my diamonds are very expensive")
        case Branch.RIGHT:
            colour = ch.recv()
            ch.send(
                f'Thanks for purchasing a {colour} diamond, you spent ${catalogue[colour]}')


if __name__ == '__main__':
    main()

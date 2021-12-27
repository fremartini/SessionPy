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
    my_balance = 50_000  # USD
    ch = Channel[Send[str, Recv[dict[DiamondColour, int],
                                Choose[Recv[str, End], Send[DiamondColour, Recv[str, End]]]]]]()
    ch.send("Hi! I'd like to purchase a diamond")
    catalogue = ch.recv()
    best_diamond = None
    for colour, price in catalogue:
        if price <= my_balance and price > catalogue[best_diamond]:
            best_diamond = colour
    if not best_diamond:
        ch.choose(Branch.LEFT)
        response = ch.recv()
        print('Response from seller:', response)
    else:
        ch.choose(Branch.RIGHT)
        ch.send(best_diamond)
        receipt = ch.recv()
        print('Receipt from seller:', receipt)


if __name__ == '__main__':
    main()

import channel
from sessiontype import *
from typechecking import verify_channels
from diamond_util import *


@verify_channels
def main():
    my_balance = 500_000  # USD
    ch = Channel[Send[str, Recv[Catalogue,Choose[Recv[str, End], Send[DiamondColour, Recv[str, End]]]]]]()
    ch.send("Hi! I'd like to purchase a diamond")
    catalogue_object : Catalogue = ch.recv()
    catalogue = dict(catalogue_object) # due to current inability to infere the dicitionary property from ST
    best_diamond: DiamondColour = None
    for colour in catalogue:
        price = catalogue.get(colour)
        if (best_diamond and price > catalogue.get(best_diamond)
            or not best_diamond and price <= my_balance):
            best_diamond = colour
    if best_diamond:
        ch.choose(Branch.RIGHT)
        ch.send(best_diamond)
        receipt : str = ch.recv()
        print('Receipt from seller:', receipt)
        my_balance -= catalogue[best_diamond]
    else:
        ch.choose(Branch.LEFT)
        response = ch.recv()
        print('Response from seller:', response)


if __name__ == '__main__':
    main()

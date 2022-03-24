if __name__ == '__main__':
    from sessiontype import *
    from diamond_util import *
    from channel import Channel, Branch

    my_balance = 500_000  # USD
    ch = Channel[Send[str, Recv[Catalogue, Choose[Recv[str, End], Send[DiamondColour, Recv[str, End]]]]]](
        ("localhost", 5000), ("localhost", 5005))
    ch.send("Hi! I'd like to purchase a diamond")
    catalogue: Catalogue = ch.recv()
    best_diamond: DiamondColour = None
    for colour in catalogue:
        price = catalogue[colour]
        if (best_diamond and price > catalogue.get(best_diamond)
                or not best_diamond and price <= my_balance):
            best_diamond = colour
    if best_diamond:
        ch.choose(Branch.RIGHT)
        ch.send(best_diamond)
        receipt: str = ch.recv()
        print('Receipt from seller:', receipt)
        my_balance -= catalogue[best_diamond]
    else:
        ch.choose(Branch.LEFT)
        response = ch.recv()
        print('Response from seller:', response)

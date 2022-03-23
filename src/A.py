if __name__ == '__main__':
    from channel import *
    from sessiontype import *

    ch = Channel[Offer[Send[str, Recv[int, End]], Send[int, End]]](('localhost', 5006), ('localhost', 5011))

    ch.send(1)

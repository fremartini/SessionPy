if __name__ == '__main__':
    from channel import *
    from sessiontype import *

    ch = Channel[Choose[Send[str, End], Send[int, End]]](('localhost', 5011), ('localhost', 5006))

    ch.choose(Branch.RIGHT)
    a = ch.recv()
    print('received ', a, type(a))



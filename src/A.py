if __name__ == '__main__':
    from channel import *
    from sessiontype import *

    ch = Channel[Send[int, End]](('localhost', 5000), ('localhost', 5001))

    ch.send(13)

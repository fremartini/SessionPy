if __name__ == '__main__':
    from channel import *
    from sessiontype import *

    ch = Channel[Send[int, End]](('localhost', 5006), ('localhost', 5011))

    a = ch.recv()
    print('received ', a)
    ch.send("hi!")

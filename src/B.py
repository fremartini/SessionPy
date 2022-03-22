if __name__ == '__main__':
    from channel import *
    from sessiontype import *

    ch = Channel[Recv[int, End]](('localhost', 5011), ('localhost', 5006))

    ch.send("hello")
    a = ch.recv()
    print('received ', a)
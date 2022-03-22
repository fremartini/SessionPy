if __name__ == '__main__':
    from channel import *
    from sessiontype import *

    ch = Channel[Recv[int, End]](('localhost', 5001), ('localhost', 5000))

    a = ch.recv()
    print('received', a)

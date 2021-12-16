from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = Channel[Send[int, Branch[Recv[str, End], Send[int, End]]]]
    ch.send(5)

    b = ch.offer()
    if isinstance(b, Branch.left):
        print("A: receiving message from client (B)")
        msg = ch.recv()
        print(f"A: received message '{msg}'")
    else:
        print("A: sending number to client (B)")
        ch.send(42)

if __name__ == '__main__':
    main()
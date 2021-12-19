from channel import *
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    ch = Channel[Send[int, Offer[Send[str, Recv[int, End]], Send[int, End]]]]()
    ch.send(5)

    match ch.offer():
        case Branch.LEFT:
            print("A: receiving message from client (B)")
            ch.send("hello!")
            msg = ch.recv()
            print(f"A: received message '{msg}'")    
            
        case Branch.RIGHT:
            print("A: sending number to client (B)")
            ch.send(42)

if __name__ == '__main__':
    main()
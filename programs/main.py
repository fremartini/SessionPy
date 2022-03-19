ch = Channel[Offer[Send[int, End], Recv[str, End]]]

match ch.offer():
    case Branch.LEFT:
        ch.send(42)
    case Branch.RIGHT:
        s = ch.recv()
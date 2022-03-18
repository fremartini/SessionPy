a = Channel[Send[int, Recv[str, End]]]

a.send(2)
a.recv()
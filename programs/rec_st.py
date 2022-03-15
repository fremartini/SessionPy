def main():

    ch = Channel[Loop[Send[Int, End]]]()

    while True:
        ch.send(42)
    

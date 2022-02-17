from channel import Branch, Channel
from sessiontype import *
from typechecking import verify_channels

@verify_channels
def main():
    
    ch = Channel[Send[int, End]]()
    ch.send(42)
    print('sent', 42)  # we expect this!

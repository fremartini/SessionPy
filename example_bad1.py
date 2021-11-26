from channel import *
from ast_playground import verify_channels

@verify_channels
def main():
    ch = Channel[Send[int, End]]()
    v = ch.recv()
    print('received', v) # should never happen


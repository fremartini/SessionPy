from channel import *
from ast_playground import verify_channels


#@check_file
@verify_channels
def main():
    ch = Channel[Send[int, End]]()
    # v = ch.recv()
    # print('received', v) # should never happen


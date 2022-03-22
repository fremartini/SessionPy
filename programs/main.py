from channel import Channel, Branch
from sessiontype import *

ch = Channel[ Send[int, Label['looping', Choose [  Send[str, Recv[bool, Send[str, 'looping']]] ,   Send[str, End]]]]]()

ch.send(42)
while True:
    ch.choose(Branch.LEFT)
    ch.send('hello')
    boolean = ch.recv()
    ch.send('world')
ch.choose(Branch.RIGHT)
ch.send('last str outside loop')

        


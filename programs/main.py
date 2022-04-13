from channel import Channel, Branch
from sessiontype import *

def fail():
    ch = Channel[Send[List[int], Send[Tuple[str, int], Send[Dict[int, float], End]]]]()
    ch.send([1, 2])
    ch.send(('cool', 42))
    ch.send({3: 'oops'})

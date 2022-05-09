from check import typecheck_file
from sessiontype import *
from channel import Channel
from typing import *

from sessiontype import *
from channel import Channel

routing = {'self': ('localhost', 50_000), 'Alice': ('localhost', 50_505)}

ch = Channel(Send[int, 'Alice', Recv[str, 'Charlie', End]], routing, static_check=False)


def func(flag, c):
    if flag:
        s = c.recv()
    else:
        c.send(42)

func(False, ch)
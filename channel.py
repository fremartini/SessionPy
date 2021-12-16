from typing import TypeVar, Generic
from sessiontype import *
from collections import deque
from enum import Enum
T = TypeVar('T')

class Branch(Enum):
    LEFT = 0
    RIGHT = 1


class Channel(Generic[T]):
    #def init(self):
    #    fsa = construct_fsa(self)
    #    self.fsa = fsa
    #    self.state = fsa[0]
    def __init__(self) -> None:
        self.queue = deque()

    def send(self, e):
        self.queue.append(e)
        return True

    def recv(self):
        if self.queue:
            return self.queue.popleft()

    def offer(self, t, e):
        ...

    def choose(self, op):
        ...

class TCPChannel(Generic[T]):
    #def init(self):
    #    fsa = construct_fsa(self)
    #    self.fsa = fsa
    #    self.state = fsa[0]
    def __init__(self) -> None:
        self.queue = deque()

    def send(self, e):
        self.queue.append(e)
        return True

    def recv(self):
        if self.queue:
            return self.queue.popleft()

    def offer(self, t, e):
        ...

    def choose(self, op):
        ...
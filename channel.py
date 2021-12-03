from typing import TypeVar, Generic
from sessiontype import *
from collections import deque

T = TypeVar('T')

"""
Channel superclass, this should never be instantiated
"""
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

    def branch(self, t, e):
        ...

    def select(self, op):
        ...
from typing import TypeVar, Generic
from sessiontype import *
from enum import Enum

T = TypeVar('T')

class Branch(Enum):
    LEFT = 0
    RIGHT = 1

class Channel(Generic[T]):
    def __init__(self) -> None:
        self.queue = []

    def send(self, e):
        self.queue.append(e)
        return True

    def recv(self):
        if self.queue:
            return self.queue.pop(0)

    def offer(self):
        return Branch(self.recv())

    def choose(self, leftOrRight):
        assert(isinstance(leftOrRight, Branch))
        return self.send(Branch(leftOrRight))
from typing import TypeVar, Generic
from sessiontype import *
from collections import deque

T = TypeVar('T')

"""
Channel superclass, this should never be instantiated
"""
class Channel(Generic[T]):
    def init(self):
        fsa = construct_fsa(self)
        self.fsa = fsa
        self.state = fsa[0]

    def send(self, e):
        ...

    def recv(self):
        ...

"""
TCP Channel for communicating via sockets
"""
class TCPChannel(Channel[T]):
    def send(self, e):
        return super().send(e)

    def recv(self):
        return super().recv()

"""
Queue Channel for local communication
"""
class QChannel(Channel[T]):
    def __init__(self) -> None:
        self.queue = deque()

    def send(self, e):
        self.queue.append(e)
        return True

    def recv(self):
        return self.queue.popleft()
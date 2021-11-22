from typing import TypeVar, Generic
from sessiontype import *


T = TypeVar('T')
class Channel(Generic[T]):
    def init(self):
        fsa = construct_fsa(self)
        self.fsa = fsa
        self.state = fsa[0]

    def send(self, e):
        ...

    def recv(self):
        ...
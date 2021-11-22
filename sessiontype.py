from channel import *
from typing import TypeVar, Generic
from inspect import *

ST = TypeVar('ST')
A = TypeVar('A')
class Send(Generic[A, ST]):
    ...
    
class Recv(Generic[A, ST]):
    ...

class End:
    ...
c : Channel[Send[int, Recv[bool, End]]] = Channel()
#Channel[Send[int, Recv[bool, End]]].__args__ => (__main__.Send[int, __main__.Recv[bool, __main__.End]],)
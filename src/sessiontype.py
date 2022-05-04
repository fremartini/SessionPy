from typing import TypeVar, Generic
from enum import Enum

ST = TypeVar('ST')
ST1 = TypeVar('ST1')
A = TypeVar('A')
Actor = TypeVar('Actor')

class Branch(str, Enum):
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'

class SessionType:
    ...


class Send(SessionType, Generic[A, Actor, ST]):
    ...


class Recv(SessionType, Generic[A, Actor, ST]):
    ...


class Offer(SessionType, Generic[Actor, ST, ST1]):
    ...

class Choose(SessionType, Generic[Actor, ST, ST1]):
    ...


class Label(SessionType, Generic[A, ST]):
    ...


class End(SessionType):
    ...


class SessionException(TypeError):
    ...



STR_ST_MAPPING = {
    'recv': Recv,
    'send': Send,
    'offer': Offer,
    'end': End,
    'choose': Choose,
    'channel': None,
    'Branch': None
}

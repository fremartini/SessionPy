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


class Offer(SessionType, Generic[Actor, A]):
    ...


class Choose(SessionType, Generic[Actor, A]):
    ...


class Label(SessionType, Generic[A, ST]):
    ...


class End(SessionType):
    ...


STR_ST_MAPPING = {
    'recv': Recv,
    'send': Send,
    'offer': Offer,
    'end': End,
    'choose': Choose,
    'endpoint': None,
    'Branch': None,
    'label': Label,
}

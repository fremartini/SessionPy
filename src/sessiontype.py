from ast import AST
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


class SessionException(TypeError):
    def __init__(self, message: str, nd:AST=None) -> None:
        if nd:
            message = f"at line {nd.lineno}: {message}"
        super().__init__(message)


STR_ST_MAPPING = {
    'recv': Recv,
    'send': Send,
    'offer': Offer,
    'end': End,
    'choose': Choose,
    'channel': None,
    'Branch': None,
    'label': Label,
}

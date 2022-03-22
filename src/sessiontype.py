from typing import TypeVar, Generic

ST = TypeVar('ST')
ST1 = TypeVar('ST1')
A = TypeVar('A')


class SessionType:
    ...


class Send(SessionType, Generic[A, ST]):
    ...


class Recv(SessionType, Generic[A, ST]):
    ...


class Offer(SessionType, Generic[ST, ST1]):
    ...


class Choose(SessionType, Generic[ST, ST1]):
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
    'Branch': None
}
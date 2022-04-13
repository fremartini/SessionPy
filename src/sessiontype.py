from typing import TypeVar, Generic

ST = TypeVar('ST')
ST1 = TypeVar('ST1')
A = TypeVar('A')
Actor = TypeVar('Actor')


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


class Send1(SessionType, Generic[A, Actor, ST]):
    ...


class Recv1(SessionType, Generic[A, Actor, ST]):
    ...


class Offer1(SessionType, Generic[ST, Actor, ST1]):
    ...


class Choose1(SessionType, Generic[ST, Actor, ST1]):
    ...


class Label1(SessionType, Generic[A, Actor, ST]):
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
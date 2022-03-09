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


class End(SessionType):
    ...

class Loop(SessionType):
    ...
    
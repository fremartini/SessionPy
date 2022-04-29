from typing import TypeVar, Generic

ST = TypeVar('ST')
ST1 = TypeVar('ST1')
A = TypeVar('A')
Actor = TypeVar('Actor')


class SessionType:
    ...


class Send(SessionType, Generic[A, ST]):
    ...

class SendA(SessionType, Generic[A, Actor, ST]):
    ...



class Recv(SessionType, Generic[A, ST]):
    ...

class RecvA(SessionType, Generic[A, Actor, ST]):
    ...



class Offer(SessionType, Generic[ST, ST1]):
    ...

class OfferA(SessionType, Generic[Actor, ST, ST1]):
    ...

class Choose(SessionType, Generic[ST, ST1]):
    ...
class ChooseA(SessionType, Generic[Actor, ST, ST1]):
    ...


class Label(SessionType, Generic[A, ST]):
    ...

class LabelA(SessionType, Generic[A, Actor, ST]):
    ...


class End(SessionType):
    ...


class SessionException(TypeError):
    ...

def has_dual(typ):
    return typ in [Send, Recv, Offer, Choose]

def get_dual(typ):
    match typ():
        case Send(): return Recv
        case Recv(): return Send 
        case Offer(): return Choose
        case Choose(): return Offer


STR_ST_MAPPING = {
    'recv': Recv,
    'send': Send,
    'offer': Offer,
    'end': End,
    'choose': Choose,
    'channel': None,
    'Branch': None
}

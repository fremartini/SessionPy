from typing import Generic, Iterable, NewType, TypeVar, Union


A = TypeVar("A") # Action
SEND = NewType("SEND", A)
RECV = NewType("RECV", A)
STOP  = NewType("STOP",  A)

T = TypeVar("T") # Type
class SessionType(Generic[A, T]): # TODO: This "class" should create an actual type
    def __init__(self) -> T:
        ...

class Channel(Iterable[SessionType]):
    ...

t1 : SessionType[SEND, int] 
t2 : SessionType[RECV, int] 
t3 : SessionType[SEND, str] 
t4 : SessionType[STOP, None] 

ch : Channel[Union[t1, Union[t2, Union[t3, t4]]]]
# same thing below, written out
ch1 : Channel[Union[SessionType[SEND, int], 
                Union[SessionType[RECV, int], 
                    Union[SessionType[SEND, str],
                          SessionType[STOP, None]]]]]


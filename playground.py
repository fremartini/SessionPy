from typing import Generic, Iterable, Iterator, NewType, TypeVar, Union


A = TypeVar("A") # Action
SEND = NewType("SEND", A)
RECV = NewType("RECV", A)
STOP  = NewType("STOP",  A)

T = TypeVar("T") # Type
class ST(Generic[A, T]): # TODO: This "class" should create an actual type
    def __init__(self) -> T:
        ...

class Channel(Iterable[ST]):
    def __init__(self, a) -> None:
        super().__init__()
        self.a = a
    def __iter__(self) -> Iterator[ST]:
        return super().__iter__()

# ST[SEND, int]
#t1 : ST[SEND, int] 
#t2 : ST[RECV, int] 
#t3 : ST[SEND, str] 
#t4 : ST[STOP, None] 

# ch : Channel[Union[t1, Union[t2, Union[t3, t4]]]]
# same thing below, written out
ch1 = Channel[ST[SEND, int] | [ST[RECV, int] | [ST[SEND, str] | ST[STOP, None]]]]()


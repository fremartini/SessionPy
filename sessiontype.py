from channel import Channel
from typing import TypeVar, Generic

ST = TypeVar('ST')
A = TypeVar('A')

class SessionType:
    ...

class Send(SessionType, Generic[A, ST]):
    ...
    
class Recv(SessionType, Generic[A, ST]):
    ...

class End(SessionType):
    ...

def is_session_type(t : type):
    return issubclass(t, SessionType)

def extract(c : Channel):
    return builder(c.__orig_class__.__args__[0]) 

def builder(st : SessionType):
    if st == End:
        return []
    action = st.__origin__
    typ, rest = st.__args__ 
    return [(action, typ)] + builder(rest)

# Exctracting type info
#c = Channel[Recv[str, Send[int, End]]]()
#typ = c.__orig_class__.__args__[0] # extract channels args where type info lies                                         => __main__.Recv[str, __main__.Send[int, __main__.End]]
#typ.__origin__ # returns currenct session type action i.e. Send, Recv or End                                            => <class '__main__.Recv'>
#typ.__args__ # this "steps into" our session type: returns tuple with (Int, {rest}) but removes outer action, i.e. Send => (<class 'str'>, __main__.Send[int, __main__.End])
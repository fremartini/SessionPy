from channel import *
from typing import TypeVar, Generic
from inspect import *

ST = TypeVar('ST')
A = TypeVar('A')
class Send(Generic[A, ST]):
    ...
    
class Recv(Generic[A, ST]):
    ...

class End:
    ...

# Exctracting type info
c = Channel[Recv[str, Send[int, End]]]()
#typ = c.__orig_class__.__args__[0] # extract channels args where type info lies
#typ.__origin__ # returns currenct session type action i.e. Send, Recv or End
#typ.__args__ # this "steps into" our session type: returns tuple with (Int, {rest}) but removes outer action, i.e. Send

def extract(c):
    return builder(c.__orig_class__.__args__[0]) 

def builder(st):
    if st == End:
        return []
    action = st.__origin__
    typ, rest = st.__args__ 
    return [(action, typ)] + builder(rest)
    
print(extract(c))
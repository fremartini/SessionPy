from typeChecking import *

"""
find some language construct that allows to do communication, 
i.e., it allows to do send and receive over something. 
This could be some Python feature.

Conversation API:

create(protocol, inv_config.yml)        # session initiation bla
join(self, role, principal_name)        # accept an invitation
send(self, to_role, op, payload)        # send a msg
recv(self, from_role)                   # receive a msg
recv_async(self, from_role, callback)   # receive asynchronously
stop()                                  # close the connection
"""

class Channel:
    def __init__(self, typ):
        self.chType = typ
        self.queue = []

    def __str__(self) -> str:
        return f"Channel{str(self.chType)} {str(self.queue)}"

def check_channel(func):
    #assert func.getArgs[1].chType == type(func.getArgs[2])
    params = inspect.signature(func).parameters
    print(params)

    ch : Channel = params['ch']
    e = params['e']

    print(type(ch))

def send(ch : Channel, e) -> str:
    # assert type(e) == ch.chType #TODO: yikes
    ch.queue.append(e)
    print(f"appended {e}: {ch.queue}")

def recv(ch : Channel):
    v = ch.queue.pop(0)
    print(f"poppped {v} from queue")
    return v
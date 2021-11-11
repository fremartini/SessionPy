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

    @typeCheck
    def send(self, e):
        self.queue.append(e)
        print(f"appended {e}: {self.queue}")

    @typeCheck
    def recv(self):
        v = self.queue.pop(0)
        print(f"poppped {v} from queue")
        return v
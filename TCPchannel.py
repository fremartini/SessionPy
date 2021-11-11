from typeChecking import *
import socket
import traceback

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
    host = 'localhost'

    def __init__(self, typ, port):
        self.chType = typ
        self.port = port

    def __str__(self) -> str:
        return f"Channel{str(self.chType)} {str(self.queue)}"

    def send(self, e):
        c : socket
        try:
            s = socket.socket()
            s.bind((Channel.host, self.port))
            s.listen()
            print (f"Waiting for someone to recieve {str(e)}")

            c, addr = s.accept()
            c.send(bytes(str(e), 'utf-8'))
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
        finally:
            c.close()

    def recv(self):
        s : socket
        try:
            #TODO: make this blocking
            s = socket.socket()
            s.connect((Channel.host, self.port))
            r = s.recv(1024)
            print (r)
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
        finally:
            s.close()
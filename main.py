from channel import *
from typeChecking import check_channels, check_file
from typing import TypeVar

from protocol import *

@check_file
def main():
    Client = TypeVar("Client")
    Server = TypeVar("Server")
    p = Protocol[(Client, Server, int), (Server, Client, int)]

    #ch : Channel[out(int), into(bool)] = Channel(5000)
    #will_send_ints(ch)

#@check_channels({'chI': int})
#def will_send_ints(chI: Channel):
#    chI.send(1)

if __name__ == '__main__':
    main()

#TODO: generics & simple communication

"""
Client -> Server : int
Server -> Client : int

from typing import TypeVar
Client = TypeVar("Client")
Server = TypeVar("Server")
p = Protocol[(Client, Server, int), (Server, Client, int)]

A:
send()
recv()

B:
recv()
send()



"""
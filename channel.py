import os
import socket
from typing import TypeVar, Generic
from conversation import send
from sessiondata import SessionData
from sessiontype import *
from collections import deque
from enum import Enum
from util import deserialize, load_router_config, serialize

T = TypeVar('T')


class Branch(Enum):
    LEFT = 0
    RIGHT = 1


class Channel(Generic[T]):
    def __init__(self) -> None:
        self.queue = []

    def send(self, e):
        self.queue.append(e)
        return True

    def recv(self):
        if self.queue:
            return self.queue.pop(0)

    def offer(self):
        v = self.recv()
        if (v == 0):
            return Branch.LEFT
        else:
            return Branch.RIGHT

    def choose(self, leftOrRight):
        assert(isinstance(leftOrRight, Branch))
        return self.send(Branch(leftOrRight))


class TCPChannel(Generic[T]):
    def __init__(self) -> None:
        yaml = load_router_config()
        self.router_host = yaml['host']
        self.router_port = yaml['port']
        self.addr = (self.router_host, self.router_port)

    def send(self, e):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(self.addr)
            msg = serialize(SessionData(self.addr, e))
            s.send(msg)

    def recv(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(self.addr)
                s.listen()
                print(f"listening on {self.addr}")
                conn, a = s.accept()
                with conn:
                    msg: SessionData = deserialize(conn.recv(1024))
                    return msg.payload
        except KeyboardInterrupt:
            os._exit(0)

    def offer(self, t, e):
        raise NotImplementedError

    def choose(self, op):
        raise NotImplementedError

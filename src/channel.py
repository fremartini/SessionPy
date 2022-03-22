import sys
import traceback
from typing import Any

from sessiontype import *
from enum import Enum
import socket

T = TypeVar('T')


class Branch(Enum):
    LEFT = 0
    RIGHT = 1


class Channel(Generic[T]):
    def __init__(self, local: tuple[str, int], remote: tuple[str, int]) -> None:
        self.local = local
        self.remote = remote

    def send(self, e: Any) -> None:
        try:
            if _is_port_listening(self.remote):
                print('sending message to ', self.remote)
                with _spawn_socket() as s:
                    s.connect(self.remote)
                    s.sendall(_encode(e))
            else:
                print('listening on ', self.local)
                with _spawn_socket() as s:
                    s.bind(self.local)
                    s.listen()
                    c, _ = s.accept()
                    with c:
                        c.sendall(_encode(e))
                        print('sent ', e)

        except KeyboardInterrupt:
            _exit()
        except Exception as ex:
            _trace(ex)

    def recv(self) -> Any:
        try:
            if _is_port_listening(self.remote):
                print('receiving from ', self.remote)
                with _spawn_socket() as s:
                    s.connect(self.remote)
                    r = s.recv(1024)
                    print('received ', r)
                    return _decode(r)
            else:
                print('listening on ', self.local)
                with _spawn_socket() as s:
                    s.bind(self.local)
                    s.listen()
                    c, _ = s.accept()
                    with c:
                        r = c.recv(1024)
                        return _decode(r)
        except KeyboardInterrupt:
            _exit()
        except Exception as ex:
            _trace(ex)

    def serv(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(self.local)
            s.listen()
            print("Server started on ", self.local)
            c, addr = s.accept()
            with c:
                data, addr = s.recvfrom(1024)
                data = data.decode('utf-8')
                print("Message from: " + str(addr))
                print("From connected user: " + data)
                data = data.upper()
                print("Sending: " + data)
                s.sendto(data.encode('utf-8'), addr)
        finally:
            s.close()

    def cli(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(self.local)

            message = input("-> ")
            s.sendto(message.encode('utf-8'), self.remote)
            data, addr = s.recvfrom(1024)
            data = data.decode('utf-8')
            print("Received from server: " + data)
        finally:
            s.close()

    def offer(self) -> None:
        ...

    def choose(self, direction: Branch) -> None:
        ...


def _is_port_listening(address: tuple[str, int]):
    s = socket.socket()
    try:
        s.connect(address)
        return True
    except socket.error:
        return False
    finally:
        s.close()


def _spawn_socket() -> socket.socket:
    s: socket = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return s


def _encode(e: Any) -> bytes:
    return bytes(str(e), 'utf-8')


def _decode(e: bytes) -> Any:
    return e.decode('utf-8')


def _trace(ex: Exception) -> None:
    traceback.print_exception(type(ex), ex, ex.__traceback__)


def _exit() -> None:
    sys.exit(0)

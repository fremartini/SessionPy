import sys
import traceback
from typing import Any
import pickle

from sessiontype import *
from enum import Enum
import socket

T = TypeVar('T')


class Branch(Enum):
    LEFT = 0
    RIGHT = 1

    def equals(self, string):
        return self.name == string


class Channel(Generic[T]):
    def __init__(self, local: tuple[str, int], remote: tuple[str, int]) -> None:
        self.local = local
        self.remote = remote

    def send(self, e: Any) -> None:
        with _spawn_socket() as client_socket:
            try:
                _wait_until_connected_to(client_socket, self.remote)

                client_socket.send(_encode(e))
            except Exception as ex:
                _trace(ex)

    def recv(self) -> Any:
        with socket.socket() as server_socket:
            try:
                server_socket.bind(self.local)

                server_socket.listen(2)
                conn, address = server_socket.accept()
                with conn:
                    data = _decode(conn.recv(1024))
                    return data
            except KeyboardInterrupt:
                _exit()
            except Exception as ex:
                _trace(ex)

    def offer(self) -> Branch:
        maybe_branch: str = self.recv()
        assert maybe_branch in ['Branch.RIGHT', 'Branch.LEFT']
        return Branch.LEFT if maybe_branch == 'Branch.LEFT' else Branch.RIGHT

    def choose(self, direction: Branch) -> None:
        assert isinstance(direction, Branch)
        self.send(direction)


def _wait_until_connected_to(sock: socket.socket, address: tuple[str, int]) -> None:
    _connected = False

    while not _connected:
        try:
            sock.connect(address)

            _connected = True
        except KeyboardInterrupt:
            _exit()
        except Exception:
            pass


def _spawn_socket() -> socket.socket:
    return socket.socket()


def _encode(e: Any) -> bytes:
    return pickle.dumps(e)


def _decode(e: bytes) -> Any:
    return pickle.loads(e)


def _trace(ex: Exception) -> None:
    traceback.print_exception(type(ex), ex, ex.__traceback__)


def _exit() -> None:
    sys.exit(0)

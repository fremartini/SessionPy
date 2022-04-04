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


class Channel(Generic[T]):
    def __init__(self, local: tuple[str, int] = None, remote: tuple[str, int] = None) -> None:
        self.local_mode = True if local is None or remote is None else False

        if self.local_mode:
            self.queue = []
        else:
            self.local = local
            self.remote = remote
            self.server_socket = _spawn_socket()
            self.server_socket.bind(self.local)

    def send(self, e: Any) -> None:
        self._send_local(e) if self.local_mode else self._send_remote(e)

    def recv(self) -> Any:
        return self._recv_local() if self.local_mode else self._recv_remote()

    def offer(self) -> Branch:
        maybe_branch: Any = self.recv()
        assert isinstance(maybe_branch, Branch)
        return maybe_branch

    def choose(self, branch: Branch) -> None:
        assert isinstance(branch, Branch)
        self.send(branch)

    def _send_local(self, e: Any) -> None:
        self.queue.append(e)

    def _recv_local(self) -> Any:
        if len(self.queue) == 0:
            while True:
                if len(self.queue) != 0:
                    break
        return self.queue.pop(0)

    def _send_remote(self, e: Any) -> None:
        with _spawn_socket() as client_socket:
            try:
                _wait_until_connected_to(client_socket, self.remote)

                client_socket.send(_encode(e))
            except Exception as ex:
                _trace(ex)

    def _recv_remote(self) -> Any:
        try:
            self.server_socket.listen()
            conn, _ = self.server_socket.accept()
            with conn:
                return _decode(conn.recv(1024))
        except KeyboardInterrupt:
            _exit()
        except Exception as ex:
            _trace(ex)

    def __del__(self):
        if not self.local_mode:
            self.server_socket.close()


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
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock


def _encode(e: Any) -> bytes:
    return pickle.dumps(e)


def _decode(e: bytes) -> Any:
    return pickle.loads(e)


def _trace(ex: Exception) -> None:
    traceback.print_exception(type(ex), ex, ex.__traceback__)


def _exit() -> None:
    sys.exit(0)

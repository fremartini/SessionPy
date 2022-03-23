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
        with _spawn_socket() as s:
            try:
                _connected = False

                print('trying to connect to ', self.remote)
                while not _connected:
                    try:
                        s.connect(self.remote)

                        _connected = True
                    except Exception:
                        pass

                print('connected to ', self.remote)
                s.send(e.encode('utf-8'))

            except KeyboardInterrupt:
                _exit()
            except Exception as ex:
                _trace(ex)

    def recv(self) -> Any:
        try:
            return self._recv()
        except KeyboardInterrupt:
            _exit()
        except Exception as ex:
            _trace(ex)

    def offer(self) -> None:
        ...

    def choose(self, direction: Branch) -> None:
        ...

    def _recv(self):
        with socket.socket() as server_socket:
            server_socket.bind(self.local)

            server_socket.listen(2)
            conn, address = server_socket.accept()
            with conn:
                data = conn.recv(1024).decode()
                return str(data)

    def _send(self, message: Any, to: tuple[str, int]):
        print('sending message to ', self.remote)
        with _spawn_socket() as s:
            s.connect(to)
            s.send(message.encode('utf-8'))


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
    # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return s


def _encode(e: Any) -> bytes:
    return bytes(str(e), 'utf-8')


def _decode(e: bytes) -> Any:
    return e.decode('utf-8')


def _trace(ex: Exception) -> None:
    traceback.print_exception(type(ex), ex, ex.__traceback__)


def _exit() -> None:
    sys.exit(0)

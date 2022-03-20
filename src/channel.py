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
    def __init__(self, address: tuple[str, int]) -> None:
        self.address = address

    def send(self, e: Any) -> None:
        s = _spawn_socket()
        try:
            # try to connect if someone is listening
            s.connect(self.address)
            s.sendall(_encode(e))
        except OSError:
            # nobody is listening, become the 'server' and wait
            s.bind(self.address)
            s.listen()
            c, _ = s.accept()
            with c:
                c.sendall(_encode(e))
        except KeyboardInterrupt:
            s.close()
            _exit()
        except Exception as ex:
            _trace(ex)

    def recv(self) -> Any:
        s = _spawn_socket()
        try:
            # try to connect to 'server' and receive message
            s.connect(self.address)
            r = s.recv(1024)
            return _decode(r)
        except OSError:
            try:
                # nobody is serving anything, become the server and wait
                s.bind(self.address)
                s.listen()
                c, _ = s.accept()
                with c:
                    r = c.recv(1024)
                    return _decode(r)
            except KeyboardInterrupt:
                sys.exit(0)
            except OSError:
                # address may already be bound, try again
                return self.recv()
            except Exception as ex:
                _trace(ex)
        except KeyboardInterrupt:
            _exit()
        except Exception as ex:
            _trace(ex)
        finally:
            s.close()

    def offer(self) -> Branch:
        ...

    def choose(self, direction: Branch) -> None:
        assert (isinstance(direction, Branch))


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

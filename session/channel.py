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
        message = str(e)
        try:
            s.bind(self.address)
            s.listen()
            print(f"Waiting for someone to receive {message}")

            c, _ = s.accept()
            with c:
                print(f"Sent {message}")
                c.send(_encode(message))

        except OSError:
            s.connect(self.address)
            print(f"Sent {message}")
            s.send(_encode(message))
        except KeyboardInterrupt:
            s.close()
            _exit()
        except Exception as ex:
            _trace(ex)

    def recv(self) -> Any:
        s = _spawn_socket()
        try:
            s.connect(self.address)
            r = s.recv(1024)
            return r
        except OSError:
            try:
                s.bind(self.address)
                s.listen()
                print(f"Waiting for someone to send a message")

                c, _ = s.accept()
                with c:
                    r = c.recv(1024)
                    return r
            except KeyboardInterrupt:
                sys.exit(0)
            except OSError:
                return self.recv()
            except Exception as ex:
                _trace(ex)
        except KeyboardInterrupt:
            _exit()
        except Exception as ex:
            _trace(ex)
        finally:
            s.close()


"""
    def offer(self):
        return Branch(self.recv())

    def choose(self, leftOrRight):
        assert (isinstance(leftOrRight, Branch))
        return self.send(Branch(leftOrRight))
"""


def _spawn_socket() -> socket.socket:
    s: socket = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return s


def _encode(e: Any) -> bytes:
    return bytes(e, 'utf-8')


def _trace(ex: Exception) -> None:
    traceback.print_exception(type(ex), ex, ex.__traceback__)

def _exit() -> None:
    sys.exit(0)

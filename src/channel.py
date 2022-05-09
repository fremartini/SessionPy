import sys
import traceback
from typing import Any, Dict
import pickle
from lib import type_to_str
from sessiontype import *
import socket
import statemachine
from statemachine import Action, BranchEdge
from check import typecheck_file

T = TypeVar('T')


class Channel(Generic[T]):
    def __init__(self, session_type, roles: Dict[str, tuple[str, int]],
                 static_check=True, dynamic_check=True) -> None:
        self.session_type = statemachine.from_generic_alias(session_type)
        self.dynamic_check = dynamic_check
        if static_check:
            typecheck_file()
            print('> Static check succeeded ✅')
        self.local = roles['self']
        self.roles = roles
        self.server_socket = _spawn_socket()
        self.server_socket.bind(self.local)

    def send(self, e: Any) -> None:
        actor = None
        if self.dynamic_check:
            nd = self.session_type
            action, actor = nd.outgoing_action(), nd.outgoing_actor()
            if action == Action.SEND and nd.outgoing_type() == type(e):
                self.session_type = nd.next_nd()
            else:
                expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
                raise RuntimeError(f'Expected to {expected_action}, tried to send {type_to_str(type(e))}')
        self._send(e, self.roles[actor])



    def recv(self) -> Any:
        if self.dynamic_check:
            nd = self.session_type
            action, actor = nd.outgoing_action(), nd.outgoing_actor()

            if action == Action.RECV:
                self.session_type = nd.next_nd()
            else:
                expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
                raise RuntimeError(f'Expected to {expected_action}, tried to receive something')
        return self._recv()

    def offer(self) -> str:
        pick : str = self._recv()
        if self.dynamic_check: 
            nd = self.session_type
            action, actor = nd.outgoing_action(), nd.outgoing_actor()
            if action == Action.BRANCH:
                for edge in nd.outgoing:
                    assert isinstance(edge, BranchEdge)
                    if edge.key == pick:
                        self.session_type = nd.outgoing[edge]
                        break
            else:
                expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
                raise RuntimeError(f'Expected to {expected_action}, offer was called')
        return pick 

    def choose(self, pick: str) -> None:
        actor = 'self'
        if self.dynamic_check:
            nd = self.session_type
            action, actor = nd.outgoing_action(), nd.outgoing_actor()
            if action == Action.BRANCH:
                for edge in nd.outgoing:
                    assert isinstance(edge, BranchEdge)
                    if edge.key == pick:
                        self.session_type = nd.outgoing[edge]
                        break
            else:
                expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
                raise RuntimeError(f'Expected to {expected_action}, choose was called')
        self._send(pick, self.roles[actor])

    def _send(self, e: Any, to : tuple[str, int]) -> None:
        with _spawn_socket() as client_socket:
            try:
                _wait_until_connected_to(client_socket, to)

                client_socket.send(_encode(e))
            except Exception as ex:
                _trace(ex)

    def _recv(self) -> Any:
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
        try:
            self.server_socket.close()
        except:
            pass


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

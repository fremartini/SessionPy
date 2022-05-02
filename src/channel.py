import sys
import traceback
from typing import Any
import pickle
from lib import Branch, type_to_str
from sessiontype import *
import socket
import statemachine
from statemachine import Action
from check import typecheck_file



T = TypeVar('T')

class Channel(Generic[T]):
    def __init__(self, session_type=Any, local: tuple[str, int] = None, remote: tuple[str, int] = None, contravariant = False, static_check=True) -> None:

        self.local_mode = True if local is None or remote is None else False
        self.session_type = statemachine.from_generic_alias(session_type) if session_type != Any else Any
        if self.session_type != Any and static_check:
            typecheck_file()
        self.contravarint = contravariant
        if self.local_mode:
            self.queue = []
        else:
            self.local = local
            self.remote = remote
            self.server_socket = _spawn_socket()
            self.server_socket.bind(self.local)

    def send(self, e: Any) -> None:
        if self.session_type != Any:
            nd = self.session_type
            if nd.outgoing_action() == Action.SEND and nd.outgoing_type() == type(e):
                self.session_type = nd.next_nd()
            else:
                expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
                raise RuntimeError(f'Expected to {expected_action}, tried to send {type_to_str(type(e))}')
        self._send_local(e) if self.local_mode else self._send_remote(e)

    def recv(self) -> Any:
        if self.session_type != Any:
            nd = self.session_type
            if nd.outgoing_action() == Action.RECV:
                self.session_type = nd.next_nd()
            else:
                expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
                raise RuntimeError(f'Expected to {expected_action}, tried to receive something')
        return self._recv_local() if self.local_mode else self._recv_remote()

    def offer(self) -> Branch:
        maybe_branch: Any = self.recv()
        assert isinstance(maybe_branch, Branch)
        if self.session_type != Any:
            nd = self.session_type
            if isinstance(nd.outgoing_action(), Branch):
                self.session_type = nd.outgoing[maybe_branch]
            else:
                expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
                raise RuntimeError(f'Expected to {expected_action}, offer was called')
        return maybe_branch

    def choose(self, branch: Branch) -> None:
        if self.session_type != Any:
            nd = self.session_type
            if nd.outgoing_action() == Action.BRANCH:
                self.session_type = nd.outgoing[branch]
            else:
                expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
                raise RuntimeError(f'Expected to {expected_action}, choose was called')
        assert isinstance(branch, Branch)
        self._send_local(branch) if self.local_mode else self._send_remote(branch)


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
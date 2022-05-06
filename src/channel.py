import sys
import traceback
import time
from typing import Any, Dict
import pickle
from lib import type_to_str
from sessiontype import *
import socket
import statemachine
from statemachine import Action
from check import typecheck_file

T = TypeVar('T')


class Channel(Generic[T]):
    def __init__(self, session_type, roles: Dict[str, tuple[str, int]],
                 static_check=True) -> None:

        self.session_type = statemachine.from_generic_alias(session_type)
        if static_check:
            typecheck_file()

        self.rolesToPorts = roles
        self.portsToRoles = {v: k for k, v in roles.items()}
        self.server_socket = _spawn_socket()
        self.server_socket.bind(roles['self'])
        self.queue = []

    def send(self, e: Any) -> None:
        nd = self.session_type
        action, actor = nd.outgoing_action(), nd.outgoing_actor()
        if action == Action.SEND and nd.outgoing_type() == type(e):
            self.session_type = nd.next_nd()
        else:
            expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
            raise RuntimeError(f'Expected to {expected_action}, tried to send {type_to_str(type(e))}')
        self._send(e, self.rolesToPorts[actor])

    def recv(self) -> Any:
        nd = self.session_type
        action, actor = nd.outgoing_action(), nd.outgoing_actor()
        if action == Action.RECV:
            self.session_type = nd.next_nd()
        else:
            expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
            raise RuntimeError(f'Expected to {expected_action}, tried to receive something')
        return self._recv(actor)

    def offer(self) -> Branch:
        nd = self.session_type
        actor = nd.outgoing_actor()
        branch : Branch = self._recv(actor)
        assert isinstance(branch, Branch)
        action = nd.outgoing_action()
        if action == Action.BRANCH:
            self.session_type = nd.outgoing[branch]
        else:
            expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
            raise RuntimeError(f'Expected to {expected_action}, offer was called')
        return branch

    def choose(self, branch: Branch) -> None:
        nd = self.session_type
        action, actor = nd.outgoing_action(), nd.outgoing_actor()
        if action == Action.BRANCH:
            self.session_type = nd.outgoing[branch]
        else:
            expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
            raise RuntimeError(f'Expected to {expected_action}, choose was called')
        assert isinstance(branch, Branch)
        self._send(branch, self.rolesToPorts[actor])

    def _send(self, e: Any, to : tuple[str, int]) -> None:
        with _spawn_socket() as client_socket:
            try:
                _wait_until_connected_to(client_socket, to)

                payload = (e, self.rolesToPorts['self'])
                client_socket.send(_encode(payload))
            except Exception as ex:
                _trace(ex)

    def _recv(self, sender: str) -> Any:
        try:
            self.server_socket.listen()
            conn, _ = self.server_socket.accept()
            with conn:
                msg, addr = _decode(conn.recv(1024))
                received_from = self.portsToRoles[addr]
                expected_recipient = sender == received_from

                if expected_recipient:
                    return msg
                else:
                    self.queue.append(msg)
                    time.sleep(2) #FIXME: wait until next actor is expected
                    return self.queue.pop(0)
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
        except:
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

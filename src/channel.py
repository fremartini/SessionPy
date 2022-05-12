import sys
import traceback
from threading import Thread
from typing import Any, Dict
import pickle
from lib import type_to_str
from sessiontype import *
import socket
from src.stack import Stack
from statemachine import Action, BranchEdge, from_generic_alias
from check import typecheck_file
from debug import debug_print

T = TypeVar('T')


class Channel(Generic[T]):
    def __init__(self, session_type, roles: Dict[str, tuple[str, int]],
                 static_check=True) -> None:
        self.session_type = from_generic_alias(session_type)

        if static_check:
            typecheck_file()
            debug_print('> Static check succeeded ✅')

        self.rolesToPorts = roles
        self.portsToRoles = {v: k for k, v in roles.items()}
        self.stack: Stack[tuple[str, str]] = Stack()

        self.server_socket = _spawn_socket()
        self.server_socket.bind(roles['self'])
        self.server_socket.settimeout(1)

        self.running = True
        Thread(target=self._listen).start()

    def send(self, e: Any) -> None:
        nd = self.session_type
        action, actor = nd.outgoing_action(), nd.outgoing_actor()
        if action == Action.SEND and nd.outgoing_type() == type(e):
            self.session_type = nd.next_nd()
        else:
            expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
            raise RuntimeError(f'Expected to {expected_action}, tried to send {type_to_str(type(e))}')
        self._send(e, self.rolesToPorts[actor])
        self._close_if_complete()

    def recv(self) -> Any:
        nd = self.session_type
        action, actor = nd.outgoing_action(), nd.outgoing_actor()

        if action == Action.RECV:
            self.session_type = nd.next_nd()
        else:
            expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
            raise RuntimeError(f'Expected to {expected_action}, tried to receive something')
        res = self._recv(actor)
        self._close_if_complete()
        return res

    def offer(self) -> str:
        nd = self.session_type
        action, actor = nd.outgoing_action(), nd.outgoing_actor()
        pick: str = self._recv(actor)
        if action == Action.BRANCH:
            for edge in nd.outgoing:
                assert isinstance(edge, BranchEdge)
                if edge.key == pick:
                    self.session_type = nd.outgoing[edge]
                    break
        else:
            expected_action = 'branch' if isinstance(nd.get_edge(), Branch) else nd.get_edge()
            raise RuntimeError(f'Expected to {expected_action}, offer was called')
        self._close_if_complete()
        return pick

    def choose(self, pick: str) -> None:
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
        self._send(pick, self.rolesToPorts[actor])
        self._close_if_complete()

    def _send(self, e: Any, to: tuple[str, int]) -> None:
        with _spawn_socket() as client_socket:
            try:
                self._wait_until_connected_to(client_socket, to)

                payload = (e, self.rolesToPorts['self'])
                client_socket.send(_encode(payload))
            except Exception as ex:
                _trace(ex)

    def _recv(self, sender: str) -> Any:
        try:
            while True:
                if self.stack.isEmpty():
                    continue

                recipient = self.stack.peek()[1]
                if recipient == sender:
                    return self.stack.pop()[0]
        except KeyboardInterrupt:
            self._exit()
        except Exception as ex:
            _trace(ex)

    def _listen(self):
        self.server_socket.listen()
        while True:
            try:
                if not self.running:
                    break
                conn, _ = self.server_socket.accept()
                with conn:
                    payload = conn.recv(1024)
                    if payload:
                        msg, addr = _decode(payload)
                        sender = self.portsToRoles[addr]
                        self.stack.push((msg, sender))
            except socket.timeout:
                pass
            except Exception as ex:
                _trace(ex)

    def _close(self):
        self.running = False
        self._send('', self.rolesToPorts['self'])

    def _close_if_complete(self):
        if self.session_type.accepting:
            self._close()

    def _wait_until_connected_to(self, sock: socket.socket, address: tuple[str, int]) -> None:
        _connected = False

        while not _connected:
            try:
                sock.connect(address)
                _connected = True
            except KeyboardInterrupt:
                self._exit()
            except:
                pass

    def _exit(self) -> None:
        self._close()
        sys.exit(0)


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

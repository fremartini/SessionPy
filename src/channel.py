import sys
import traceback
from threading import Thread
from types import GenericAlias
from typing import Any, Dict
import pickle
from lib import type_to_str
from sessiontype import *
import socket
from stack import Stack
from statemachine import Action, BranchEdge, from_generic_alias, Node
from check import typecheck_file
from debug import debug_print

T = TypeVar('T')


class Channel(Generic[T]):
    """Represents the communication in a MPST protocol

    Attributes
    ----------
    session_type: Node
        state machine of the given session type
    rolesToPorts: Dict[str, tuple[str, int]
        dictionary mapping roles to their address
    portsToRoles: Dict[tuple[str, int],str]
        reverse of rolesToPorts, maps addresses to their roles
    stack: Stack
        a stack of (message, role) tuples
    server_socket: socket.socket
        socket listening for messages sent to this channels local address
    running:
        flag indicating if the channel is currently listening on its local address
    """

    def __init__(self, session_type: GenericAlias, roles: Dict[str, tuple[str, int]],
                 static_check=True) -> None:
        """
        Parameters
        ----------
        session_type: GenericAlias
            session type from which a statemachine should be built
        roles: Dict[str, tuple[str, int]
            dictionary mapping roles to their address
        static_check: bool
            indicator if this channel should be statically checked
        """

        self.session_type: Node = from_generic_alias(session_type)

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
        """Send a message to the recipient specified in the session type

        Parameters
        ----------
        e: Any
            the message to be sent
        """
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
        """Receive a message from the role specified in the session type

        Returns
        -------
        Any
            the message that was received
        """
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
        """Offer several choices to the actor specified in the session type

        Returns
        -------
        str
            the label of the branch that was picked
        """
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
        """Choose among several offers received

        Parameters
        ----------
        pick: str
            the label of the branch that is to be chosen
        """
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
        """Sends a message to a recipient over a socket.
        Blocks until it is able to establish a connection

        Parameters
        e: Any
            the message to be sent

        to: tuple[str, str]
            address of the recipient
        """
        with _spawn_socket() as client_socket:
            try:
                self._wait_until_connected_to(client_socket, to)

                payload = (e, self.rolesToPorts['self'])
                client_socket.send(_encode(payload))
            except Exception as ex:
                _trace(ex)

    def _recv(self, sender: str) -> Any:
        """Attempt to retrieve a message addressed to a given actor

        Parameters
        ----------
        sender: str
            the role of the message that is to be retrieved

        Returns
        -------
        Any
            the retrieved message
        """
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
        """Listens on the assigned local port for messages and put them in a stack"""
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
        """Close the listener on the local port.
        Sets the 'running' flag to false and sends a message to itself to terminate the listener
        """
        self.running = False
        self._send('', self.rolesToPorts['self'])

    def _close_if_complete(self):
        """Close the listener if the session type is exhausted of operations"""
        if self.session_type.accepting:
            self._close()

    def _wait_until_connected_to(self, sock: socket.socket, address: tuple[str, int]) -> None:
        """Blocks until a connection can be made

        Parameters
        ----------
        sock: socket.socket
            the socket on which the connection should be attempted

        address: tuple[str, int]
            the address that the connection should be made to
        """
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
        """Used on KeyboardInterrupts. Closes the listener and exits the program"""
        self._close()
        sys.exit(0)


def _spawn_socket() -> socket.socket:
    """Create a socket with predetermined options"""
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock


def _encode(e: Any) -> bytes:
    """Encode a message to bytes

    Parameters
    ----------
    e: Any
        the message to be encoded

    Returns
    -------
    bytes
        the bytes of 'e'
    """
    return pickle.dumps(e)


def _decode(e: bytes) -> Any:
    """Decode a message in bytes format

    Parameters
    ----------
    e: bytes
        the bytes of what should be decoded

    Returns
    -------
    Any
        the original object that was encoded using _encode
    """
    return pickle.loads(e)


def _trace(ex: Exception) -> None:
    """Print the stacktrace of an exception to the console

    Parameters
    ----------
    ex: Exception
        the exception that should have its stacktrace printed

    """
    traceback.print_exception(type(ex), ex, ex.__traceback__)

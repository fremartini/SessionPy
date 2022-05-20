from typing import Dict

from parser import *
from immutable_list import ImmutableList


class Projector:
    """Exposes functionality to project global protocols to local protocols and
    local protocols to Python files
    """

    def __init__(self):
        self._current_role = None

    def project(self, root: Protocol) -> List[str] | str:
        """Project the AST of a global or local protocol

        Parameters
        ----------
        root: Protocol
            the root node of the AST that should be parsed

        Returns
        -------
        List[str]
            a list of local protocols that were projected from the global protocol
        str
            the Python file name of the local protocol that was projected
        """
        match root.protocol:
            case p if isinstance(p, P):
                return self._project_p(p, root.typedef)
            case l if isinstance(l, L):
                return self._project_l(l, root.typedef)

    def _project_p(self, protocol: P, typedefs: List[TypeDef]) -> List[str]:
        """Write the projection of a global protocol to their corresponding local protocols

        Parameters
        ----------
        protocol: P
            the global protocol to project
        typedefs: List[TypeDef]
            the typedefs contained within the protocol

        Returns
        -------
        List[str]
            a list of local protocols that were projected from the global protocol
        """
        roles: List[str] = protocol.roles.visit()
        file_names = [f'{protocol.protocol_name.visit()}_{x}.scr' for x in roles]

        for idx, role in enumerate(roles):
            with open(file_names[idx], "w+") as f:
                self._current_role = role

                # write typedefs
                for typedef in typedefs:
                    f.write(f'{_project_typedef(typedef)}\n')

                # write header
                role_str = ''.join([f'role {x},' for x in roles])  # role X, role Y, role Z,
                role_str = role_str[:-1]  # remove trailing comma
                f.write(f'local protocol {protocol.protocol_name} at {role}({role_str}) {{\n')

                # write body
                for g in protocol.g:
                    to_write: str | None = self._project_g(g)
                    if to_write is not None:
                        f.write(f'{to_write}\n')
                f.write('}')

        return file_names

    def _project_g(self, g: G) -> str | None:
        """Project a G AST node into a string if possible

        Parameters
        ----------
        g: G
            AST node

        Returns
        -------
        str
            correctly formatted session type
        None
            session type that should not be written
        """
        match g.g:
            case global_interaction if isinstance(global_interaction, GlobalInteraction):
                return self._project_global_interaction(global_interaction)
            case global_choice if isinstance(global_choice, GlobalChoice):
                return self._project_global_choice(global_choice)
            case global_recursion if isinstance(global_recursion, GlobalRecursion):
                return self._project_global_recursion(global_recursion)
            case call if isinstance(call, Call):
                return _project_call(call)
            case end if isinstance(end, End):
                return 'End;'

    def _project_global_interaction(self, gi: GlobalInteraction) -> str | None:
        """Project a GlobalInteraction AST node

        Parameters
        ----------
        gi: GlobalInteraction
            AST node

        Returns
        -------
        str
            session type in format 'M(X) to/from ROLE'
        None
            if the role is not part of the interaction
        """

        # this role is not in the current interaction
        if self._current_role not in [gi.sender.identifier, gi.recipient.identifier]:
            return None

        if gi.sender.identifier == self._current_role:
            action = f'to {gi.recipient.identifier}'
        else:
            action = f'from {gi.sender.identifier}'

        return f'{gi.message.label.identifier}({gi.message.payload.visit()}) {action};'

    def _project_global_branch(self, gb: GlobalBranch) -> str:
        """Project a GlobalBranch AST node

        Parameters
        ----------
        gb: GlobalBranch
            AST node

        Returns
        -------
        str
            session type in format '@label; {ST}'
        """
        st = ''
        for g in gb.g:
            to_write = self._project_g(g)
            if to_write is not None:
                st = st + to_write + '\n'

        st = f'@{gb.label.label};\n{st}'
        return st

    def _project_global_choice(self, gc: GlobalChoice) -> str | None:
        """Project a GlobalChoice AST node

        Parameters
        ----------
        gc: GlobalChoice
            AST node

        Returns
        -------
        str
            session type in format 'offer to / choice from ROLE {ST} or {ST} ...'
        None
            if the role is not part of the interaction
        """
        if self._current_role not in [gc.sender.identifier, gc.recipient.identifier]:
            return None

        if self._current_role == gc.sender.identifier:
            lines = f'offer to {gc.recipient.identifier} {{\n'
        else:
            lines = f'choice from {gc.sender.identifier} {{\n'

        lines = lines + self._project_global_branch(gc.b)
        lines = lines + '}'

        for c in gc.bn:
            lines = lines + ' or {\n'
            lines = lines + self._project_global_branch(c)
            lines = lines + '}'

        return lines

    def _project_global_recursion(self, gr: GlobalRecursion) -> str:
        """Project a GlobalRecursion AST node

        Parameters
        ----------
        gr: GlobalRecursion
            AST node

        Returns
        -------
        str
            session type in format 'rec {ST}'
        """
        lines = f'rec {gr.identifier.visit()} '
        lines = lines + '{\n'

        for s in gr.g:
            to_write = self._project_g(s)
            if to_write is not None:
                lines = lines + to_write + '\n'

        lines = lines + '}'

        return lines

    def _project_l(self, protocol: L, typedefs: List[TypeDef]) -> str:
        """Write the projection of a local protocol to its corresponding Python file

        Parameters
        ----------
        protocol: L
            the local protocol to project
        typedefs: List[TypeDef]
            the typedefs contained within the protocol

        Returns
        -------
        str
            the projected Python file
        """
        role: str = protocol.perspective.visit()
        file = f'{protocol.protocol_name.visit()}_{role}.py'

        # create type mapping, ex: {'message': 'str"}
        self.type_mapping: Dict[str, str] = {}
        for typedef in typedefs:
            self.type_mapping[typedef.identifier.visit()] = typedef.typ.visit()

        with open(file, "w+") as f:
            f.write('from channel import Channel\n')
            f.write('from sessiontype import *\n\n')

            # create a routing table mapping roles to their address
            routing_table = _project_roles(role, protocol.roles.visit())
            f.write(f'routing_table = {routing_table}\n\n')

            # project the statements of the local protocol into a single session type
            session_type = self._project_session_type(protocol.t) + _closing_brackets(protocol.t)
            f.write(f'ch = Channel({session_type}, routing_table)\n')

        return file

    def _project_t(self, t: T) -> str:
        """Project a T AST node

        Parameters
        ----------
        t: T
            AST node

        Returns
        -------
        str
            correctly formatted session type
        """
        match t.op:
            case local_send if isinstance(local_send, LocalSend):
                return self._project_local_send(local_send)
            case local_recv if isinstance(local_recv, LocalRecv):
                return self._project_local_recv(local_recv)
            case local_choice if isinstance(local_choice, LocalChoice):
                return self._project_local_choice(local_choice)
            case local_recursion if isinstance(local_recursion, LocalRecursion):
                return self._project_local_recursion(local_recursion)
            case call if isinstance(call, Call):
                return f'"{call}"'
            case end if isinstance(end, End):
                return 'End'

    def _project_local_send(self, ls: LocalSend) -> str:
        """Project a LocalSend AST node

        Parameters
        ----------
        ls: LocalSend
            AST node

        Returns
        -------
        str
            session type in format 'Send[{TYP}, {ROLE}, {ST}'
        """
        typ = self._lookup_or_self(ls.message.payload.visit())
        return f"Send[{typ}, '{ls.identifier.visit()}', "

    def _project_local_recv(self, lr: LocalRecv) -> str:
        """Project a LocalSend AST node

        Parameters
        ----------
        lr: LocalRecv
            AST node

        Returns
        -------
        str
            session type in format 'Recv[{TYP}, {ROLE}, {ST}'
        """
        typ = self._lookup_or_self(lr.message.payload.visit())
        return f"Recv[{typ}, '{lr.identifier.visit()}', "

    def _project_local_branch(self, lb: LocalBranch) -> str:
        """Project a LocalBranch AST node

        Parameters
        ---------
        lb: LocalBranch
            AST node

        Returns
        -------
        str
            session type in format '"label": {ST}'
        """
        st = f'"{lb.label.visit()}": '
        for t in lb.t:
            st = st + self._project_t(t)

        st = st + _closing_brackets(lb.t)
        return st

    def _project_local_choice(self, c: LocalChoice) -> str:
        b1 = self._project_local_branch(c.b)
        st = '{'
        st = st + f'{b1}'
        for b in c.bn:
            st = st + ', ' + self._project_local_branch(b)
        st = st + '}'

        if c.op == 'offer':
            return f"Choose['{c.identifier.visit()}', {st}]"
        elif c.op == 'choice':
            return f"Offer['{c.identifier.visit()}', {st}]"
        else:
            raise Exception(f'unknown operation {c.op}')

    def _project_local_recursion(self, lr: LocalRecursion) -> str:
        """Project a LocalRecursion AST node

        Parameters
        ----------
        lr: LocalRecursion
            AST node

        Returns
        -------
        str
            session type in format 'Label["Label", {ST}]'
        """
        st = self._project_session_type(lr.t)
        st = st + _closing_brackets(lr.t)

        return f'Label["{lr.identifier.visit()}", {st}'

    def _project_session_type(self, ts: List[T]) -> str:
        """Build a string from a list of T AST nodes

        Parameters
        ----------
        ts: List[T]
            AST nodes that should be converted to a string

        Returns
        -------
        str
            ts converted to a string without closing brackets
        """
        return ImmutableList(ts).fold(lambda acc, t: acc + self._project_t(t), '')

    def _lookup_or_self(self, t: str) -> str:
        """Attempts a lookup for t in type_mappings

        Parameters
        ----------
        t: str
            key

        Returns
        -------
        str
            value of key t if it exists, otherwise returns t
        """
        try:
            return self.type_mapping[t]
        except:
            return t


def _project_typedef(t: TypeDef) -> str:
    """Project a TypeDef AST node into a string

    Parameters
    ----------
    t: TypeDef
        AST node

    Returns
    -------
    str
        string representation of TypeDef AST node
    """
    return f'type <{t.typ.visit()}> as {t.identifier.visit()};'


def _project_call(c: Call) -> str:
    """Project a Call AST node into a string

    Parameters
    ----------
    c: Call
        AST node

    Returns
    -------
    str
        string representation of Call AST node
    """
    return f'continue {c.identifier.visit()};'


def _closing_brackets(ts: List[T]) -> str:
    """Returns a sequence of closing square brackets determined by the length of ts

    Parameters
    ----------
    ts: List[T]
        list of statements that should be matched with a corresponding amount of closing brackets

    Returns
    -------
    str
        the appropriate number of closing brackets based on ts
    """
    braces_to_insert = ImmutableList(ts).map(
        lambda i:
        isinstance(i.op, LocalChoice) or
        isinstance(i.op, GlobalChoice) or
        isinstance(i.op, End) or
        isinstance(i.op, Call)).filter(lambda x: not x).len()

    return ']' * braces_to_insert


def _project_roles(me: str, roles: List[str]) -> str:
    """Create a routing table for all the roles in the protocol

    Parameters
    ----------
    me: str
        the current role being generated
    roles: List[str]
        all roles in the local protocol

    Returns
    -------
    str
        string version of a dictionary mapping roles to addresses
    """
    address = ('localhost', 0)

    lines = '{'
    for role in roles:
        if role == me:
            to_append = f"'self': {address}, "
        else:
            to_append = f"'{role}': {address}, "
        lines = lines + to_append

    lines = lines[:-2]  # remove trailing comma
    lines = lines + '}'
    return lines

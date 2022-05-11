from parser import *


class Projector:
    def __init__(self):
        self.current_role = None

    def project(self, root: Protocol) -> List[str] | str:
        match root.protocol:
            case g if isinstance(g, P):
                return self._project_p(g, root.typedef)
            case l if isinstance(l, L):
                return self._project_l(l, root.typedef)

    def _project_p(self, protocol: P, typedefs: List[TypeDef]) -> List[str]:
        roles = protocol.roles.visit()
        for r in roles:
            with open(f'{protocol.protocol_name.visit()}_{r}.scr', "w+") as f:
                self.current_role = r

                for t in typedefs:
                    f.write(self._project_typedef(t))

                role_str = remove_last_char(''.join([f'role {x},' for x in roles]))
                f.write(f'local protocol {protocol.protocol_name.identifier} at {r}({role_str}) {{ \n')

                for g in protocol.g:
                    to_write = self._project_g(g)
                    if to_write is not None:
                        f.write(f'{to_write}\n')
                f.write('}')
        return [f'{protocol.protocol_name.visit()}_{x}.scr' for x in roles]

    def _project_g(self, g: G) -> str | None:
        match g.g:
            case global_interaction if isinstance(global_interaction, GlobalInteraction):
                return self._project_global_interaction(global_interaction)
            case global_choice if isinstance(global_choice, GlobalChoice):
                return self._project_global_choice(global_choice)
            case global_recursion if isinstance(global_recursion, GlobalRecursion):
                return self._project_global_recursion(global_recursion)
            case call if isinstance(call, Call):
                return self._project_call(call)
            case end if isinstance(end, End):
                return 'End;'

    def _project_global_interaction(self, i: GlobalInteraction):
        if self.current_role not in [i.sender.identifier, i.recipient.identifier]:
            return None

        if i.sender.identifier == self.current_role:
            remainder = f'to {i.recipient.identifier}'
        else:
            remainder = f'from {i.sender.identifier}'

        return f'{i.message.label.identifier}({i.message.payload.identifier}) {remainder};'

    def _project_global_branch(self, b: GlobalBranch) -> str:
        st = ''
        for g in b.g:
            st = st + self._project_g(g) + '\n'
        st = f'@{b.label.label.visit()};\n{st}'
        return st

    def _project_global_choice(self, c: GlobalChoice) -> str | None:
        if self.current_role not in [c.sender.identifier, c.recipient.identifier]:
            return None

        if self.current_role == c.sender.identifier:
            lines = f'offer to {c.recipient.identifier} {{\n'
        else:
            lines = f'choice from {c.sender.identifier} {{\n'

        lines = lines + self._project_global_branch(c.b1)
        lines = lines + '} or {\n'
        lines = lines + self._project_global_branch(c.b2)
        lines = lines + '}'

        for c in c.bn:
            lines = lines + ' or {\n'
            lines = lines + self._project_global_branch(c)
            lines = lines + '}\n'

        return lines

    def _project_global_recursion(self, r: GlobalRecursion) -> str:
        lines = f'rec {r.identifier.visit()} '
        lines = lines + '{\n'

        for s in r.g:
            to_write = self._project_g(s)
            if to_write is not None:
                lines = lines + to_write + '\n'

        lines = lines + '}'

        return lines

    def _project_l(self, protocol: L, typedefs: List[TypeDef]) -> str:
        role = protocol.perspective.visit()
        file = f'{protocol.protocol_name.visit()}_{role}.py'

        self.type_mapping = {}
        for ty in typedefs:
            self.type_mapping[ty.identifier.visit()] = ty.typ.visit()

        with open(file, "w+") as f:
            f.write('from channel import Channel\n')
            f.write('from sessiontype import *\n\n')

            session_type = self._project_session_type(protocol.t)
            role_mapping = self._project_roles(role, protocol.roles.visit())
            f.write(f'roles = {role_mapping}\n\n')
            f.write(f'ch = Channel({session_type}, roles)\n')

        return file

    def _project_roles(self, me : str, roles: List[str]) -> str:
        lines = '{'
        address = ('localhost', 0)

        for role in roles:
            if role == me:
                to_append = f"'self': {address}, "
            else:
                to_append = f"'{role}': {address}, "
            lines = lines + to_append

        lines = remove_last_char(lines)
        lines = lines + '}'
        return lines

    def _project_t(self, t: T) -> str:
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

    def _project_local_send(self, s: LocalSend) -> str:
        typ = self._lookup_or_self(s.message.payload.visit())
        return f"Send[{typ}, '{s.identifier.visit()}', {'End' if self.insert_end else ''}"

    def _project_local_recv(self, r: LocalRecv) -> str:
        typ = self._lookup_or_self(r.message.payload.visit())
        return f"Recv[{typ}, '{r.identifier.visit()}', {'End' if self.insert_end else ''}"

    def _project_local_branch(self, b: LocalBranch) -> str:
        st = f'"{b.label.visit()}": '
        for t in b.t:
            st = st + self._project_t(t)

        st = st + self._parens(b.t)
        return st

    def _project_local_choice(self, c: LocalChoice) -> str:
        b1 = self._project_local_branch(c.b1)
        b2 = self._project_local_branch(c.b2)
        st = '{'
        st = st + f'{b1}, {b2}'
        for b in c.bn:
            st = st + ', ' + self._project_local_branch(b)
        st = st + '}'

        if c.op == 'offer':
            return f"Offer['{c.identifier.visit()}', {st}]"
        elif c.op == 'choice':
            return f"Choose['{c.identifier.visit()}', {st}]"
        else:
            raise Exception(f'unknown operation {c.op}')

    def _project_local_recursion(self, r: LocalRecursion) -> str:
        st = self._project_session_type(r.t)
        return f'Label["{r.identifier.visit()}", {st}'

    def _project_session_type(self, ts: List[T]) -> str:
        st = ''
        for (idx, t) in enumerate(ts):
            self.insert_end = idx == len(ts) - 1 and not isinstance(t.op, LocalChoice)
            st = st + self._project_t(t)
        st = st + self._parens(ts)
        return st

    def _project_typedef(self, t: TypeDef) -> str:
        return f'type <{t.typ.identifier}> as {t.identifier.identifier};\n'

    def _project_call(self, c: Call) -> str:
        return f'continue {c.identifier.visit()};'

    def _parens(self, ts: List[T]) -> str:
        parens = ''
        for i in ts:
            if isinstance(i.op, LocalChoice) or isinstance(i.op, GlobalChoice) or isinstance(i.op, End) or isinstance(i.op, Call):
                continue
            parens = parens + ']'
        return parens

    def _lookup_or_self(self, t: str) -> str:
        try:
            return self.type_mapping[t]
        except:
            return t


def remove_last_char(s: str) -> str:
    return s[:-1]

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
            with open(f'{r}.scr', "w+") as f:
                self.current_role = r

                for t in typedefs:
                    f.write(self._project_typedef(t))

                role_str = ''.join([f'role {x},' for x in roles])[:-1]
                f.write(f'local protocol {protocol.protocol_name.identifier} at {r}({role_str}) {{ \n')

                for g in protocol.g:
                    to_write = self._project_g(g)
                    if to_write is not None:
                        f.write(f'{to_write}\n')
                f.write('}')
        return [f'{x}.scr' for x in roles]

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

    def _project_global_choice(self, c: GlobalChoice) -> str | None:
        if self.current_role not in [c.sender.identifier, c.recipient.identifier]:
            return None

        if self.current_role == c.sender.identifier:
            lines = f'offer to {c.recipient.identifier} {{\n'
        else:
            lines = f'choice from {c.sender.identifier} {{\n'

        for s in c.g1:
            to_write = self._project_g(s)
            if to_write is not None:
                lines = lines + to_write + '\n'

        lines = lines + '} or {\n'

        for s in c.g2:
            to_write = self._project_g(s)
            if to_write is not None:
                lines = lines + to_write + '\n'

        lines = lines + '}'

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

        self.type_mapping = {}
        for ty in typedefs:
            self.type_mapping[ty.identifier.visit()] = ty.typ.visit()

        with open(f'{role}.py', "w+") as f:
            f.write('from channel import Channel\n')
            f.write('from sessiontype import *\n\n')

            session_type = ''
            for (idx, t) in enumerate(protocol.t):
                self.insert_end = idx == len(protocol.t) -1 and not isinstance(t.op, LocalChoice)
                session_type = session_type + self._project_t(t)

            session_type = session_type + self._parens(protocol.t)

            f.write(f'ch = Channel[{session_type}]()\n')

        return f'{role}.py'

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
                return f'"{call.identifier.visit()}"'
            case end if isinstance(end, End):
                return 'End'

    def _project_local_send(self, s: LocalSend) -> str:
        typ = self.type_mapping[s.message.payload.visit()]
        return f'Send[{typ}, {"End" if self.insert_end else ""}'

    def _project_local_recv(self, r: LocalRecv) -> str:
        typ = self.type_mapping[r.message.payload.visit()]
        return f'Recv[{typ}, {"End" if self.insert_end else ""}'

    def _project_local_choice(self, c: LocalChoice) -> str:
        def _choice(ts: List[T]) -> str:
            st = ''
            for t in ts:
                st = st + self._project_t(t)

            st = st + self._parens(ts)
            return st

        left_st = _choice(c.t1)
        right_st = _choice(c.t2)

        match c.op:
            case 'offer':
                return f'Offer[{left_st}, {right_st}]'
            case 'choice':
                return f'Choose[{left_st}, {right_st}]'

    def _project_local_recursion(self, r: LocalRecursion) -> str:

        st = ''
        for (idx, t) in enumerate(r.t):
            self.insert_end = idx == len(r.t) - 1 and not isinstance(t.op, LocalChoice)
            st = st + self._project_t(t)

        st = st + self._parens(r.t)

        return f'Label["{r.identifier.visit()}", {st}'

    def _project_typedef(self, t: TypeDef) -> str:
        return f'type <{t.typ.identifier}> as {t.identifier.identifier};\n'

    def _project_call(self, c: Call) -> str:
        return f'continue {c.identifier.visit()};'

    def _parens(self, ts: List[T]) -> str:
        parens = ''
        for i in ts:
            i = i.op
            if isinstance(i, LocalChoice) or isinstance(i, GlobalChoice) or isinstance(i, End) or isinstance(i, Call):
                continue
            parens = parens + ']'
        return parens

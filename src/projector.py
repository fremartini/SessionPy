from parser import GlobalAction, Protocol, GlobalProtocol, LocalProtocol, LocalStatement, LocalChoice, GlobalStatement, \
    LocalAction, GlobalChoice, Recurse, GlobalTransmit, LocalTransmit, End


class Projector:
    def __init__(self):
        self.current_role = None

    def project(self, root: Protocol):
        match root.protocol:
            case g if isinstance(g, GlobalProtocol):
                self._project_global_protocol(root)
            case l if isinstance(l, LocalProtocol):
                self._project_local_protocol(root)

    def _project_global_protocol(self, root: Protocol):
        roles = root.protocol.roles.visit()
        for r in roles:
            with open(f'{r}.scr', "w+") as f:
                self.current_role = r

                for t in root.typedef:
                    f.write(f'type <{t.typ.identifier}> as {t.identifier.identifier};\n')

                role_str = ''.join([f'role {x},' for x in roles])[:-1]
                f.write(f'local protocol {root.protocol.protocol_name.identifier} at {r}({role_str}) {{ \n')

                for s in root.protocol.statements:
                    to_write = self._project_global_statement(s)
                    if to_write is not None:
                        f.write(f'{to_write}\n')

                f.write('}')

    def _project_local_protocol(self, protocol: Protocol):
        roles = protocol.roles.visit()
        for r in roles:
            with open(f'{r}.py', "w") as f:
                for s in protocol.statements:
                    self._project_local_statement(s)

    def _project_local_statement(self, s: LocalStatement):
        match s.statement:
            case local_choice if isinstance(local_choice, LocalChoice):
                self._project_local_choice(local_choice)
            case local_action if isinstance(local_action, LocalAction):
                self._project_local_action(local_action)

    def _project_global_statement(self, s: GlobalStatement) -> str | None:
        match s.statement:
            case global_choice if isinstance(global_choice, GlobalChoice):
                return self._project_global_choice(global_choice)
            case global_action if isinstance(global_action, GlobalAction):
                return self._project_global_action(global_action)

    def _project_local_choice(self, c: LocalChoice) -> str:
        ...

    def _project_global_choice(self, c: GlobalChoice) -> str | None:
        if self.current_role not in [c.sender.identifier, c.recipient.identifier]:
            return None

        if self.current_role == c.sender.identifier:
            lines = f'offer to {c.recipient.identifier} {{\n'
        else:
            lines = f'choice from {c.sender.identifier} {{\n'

        for s in c.statementsDO:
            to_write = self._project_global_statement(s)
            if to_write is not None:
                lines = lines + to_write + '\n'

        lines = lines + '} or {\n'

        for s in c.statementsOR:
            to_write = self._project_global_statement(s)
            if to_write is not None:
                lines = lines + to_write + '\n'

        lines = lines + '}'

        return lines

    def _project_local_action(self, a: LocalAction) -> str:
        match a.action:
            case recurse if isinstance(recurse, Recurse):
                return f'do {recurse.identifier};'
            case local_transmit if isinstance(local_transmit, LocalTransmit):
                return self._project_local_transmit(local_transmit)
            case end if isinstance(end, End):
                return 'End;'

    def _project_global_action(self, a: GlobalAction) -> str | None:
        match a.action:
            case recurse if isinstance(recurse, Recurse):
                return f'do {recurse.identifier};'
            case global_transmit if isinstance(global_transmit, GlobalTransmit):
                return self._project_global_transmit(global_transmit)
            case end if isinstance(end, End):
                return 'End;'

    def _project_local_transmit(self, t: LocalTransmit) -> str:
        ...

    def _project_global_transmit(self, t: GlobalTransmit) -> str | None:
        if self.current_role not in [t.sender.identifier, t.recipient.identifier]:
            return None

        if t.sender.identifier == self.current_role:
            remainder = f'to {t.recipient.identifier}'
        else:
            remainder = f'from {t.sender.identifier}'

        return f'{t.message.label.identifier}({t.message.payload.identifier}) {remainder};'

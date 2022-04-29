from parser import *


class Projector:
    def __init__(self):
        self.current_role = None

    def project(self, root: Protocol):
        match root.protocol:
            case g if isinstance(g, P):
                self._project_p(g, root.typedef)
            case l if isinstance(l, L):
                ...

    def _project_p(self, protocol: P, typedefs: List[TypeDef]):
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
                return self._project_end()

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

    def _project_typedef(self, t: TypeDef) -> str:
        return f'type <{t.typ.identifier}> as {t.identifier.identifier};\n'

    def _project_call(self, c: Call) -> str:
        return f'continue {c.identifier.visit()};'

    def _project_end(self) -> str:
        return 'End;'

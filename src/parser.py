from lexer import Token, TokenType

from typing import List

"""
protocol            -> typedef* (P | L)

P                   -> "global" "protocol" identifier "(" roles ")" "{" G* "}"
G                   -> global_interaction | global_choice | global_recursion | call | end

global_interaction  -> message "from" identifier "to" identifier ";"
global_choice       -> "choice" "from" identifier "to" identifier "{" G* "}" "or" "{" G* "}"
global_recursion    -> "rec" identifier "{" G* "}"

L                   -> "local" "protocol" identifier "at" identifier "(" roles ")" "{" T* "}"
T                   -> local_send | local_recv | local_choice | local_recursion | call | end

local_send          -> message "to" identifier ";"
local_recv          -> message "from" identifier ";"
local_choice        -> ("offer" "to" | "choice" "from") identifier "{" T* "}" "or" "{" T* "}"
local_recursion     -> "rec" identifier "{" T* "}"

message             -> identifier "(" identifier ")";
typedef             -> "type" "<" identifier ">" "as" identifier ";"
roles               -> role ("," role)*
role                -> "role" identifier
call                -> "continue" identifier ";"
identifier          -> [A-Z] ([A-Z] | [a-z] | 0 - 9)*
end                 -> "End" ";"
"""


class End:
    ...


class Identifier:
    def __init__(self, identifier: str):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier


class Call:
    def __init__(self, identifier: Identifier):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier.visit()


class Role:
    def __init__(self, identifier: Identifier):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier.visit()


class Roles:
    def __init__(self, roles: List[Role]):
        self.roles = roles

    def visit(self) -> List[str]:
        return [i.visit() for i in self.roles]


class TypeDef:
    def __init__(self, typ: Identifier, identifier: Identifier):
        self.typ = typ
        self.identifier = identifier


class Message:
    def __init__(self, label: Identifier, payload: Identifier):
        self.label = label
        self.payload = payload


class LocalRecursion:
    def __init__(self, identifier: Identifier, t: List):
        self.identifier = identifier
        self.t = t


class LocalChoice:
    def __init__(self, identifier: Identifier, op: str, t1: List, t2: List):
        self.identifier = identifier
        self.op = op
        self.t1 = t1
        self.t2 = t2


class LocalRecv:
    def __init__(self, message: Message, identifier: Identifier):
        self.message = message
        self.identifier = identifier


class LocalSend:
    def __init__(self, message: Message, identifier: Identifier):
        self.message = message
        self.identifier = identifier


class T:
    def __init__(self, op: LocalSend | LocalRecv | LocalChoice | LocalRecursion | Call | str):
        self.op = op


class L:
    def __init__(self, protocol_name: Identifier, perspective: Identifier, roles: Roles,
                 t: List[T]):
        self.protocol_name = protocol_name
        self.perspective = perspective
        self.roles = roles
        self.t = t


class GlobalRecursion:
    def __init__(self, identifier: Identifier, g: List):
        self.identifier = identifier,
        self.g = g


class GlobalChoice:
    def __init__(self, sender: Identifier, recipient: Identifier, g1, g2):
        self.sender = sender
        self.recipient = recipient
        self.g1 = g1
        self.g2 = g2


class GlobalInteraction:
    def __init__(self, message: Message, sender: Identifier, recipient: Identifier):
        self.message = message
        self.sender = sender
        self.recipient = recipient


class G:
    def __init__(self, g: GlobalInteraction | GlobalChoice | GlobalRecursion | Call):
        self.g = g


class P:
    def __init__(self, protocol_name: Identifier, roles: Roles, g: List[G]):
        self.protocol_name = protocol_name
        self.roles = roles
        self.g = g


class Protocol:
    def __init__(self, typedef: List[TypeDef], protocol: P | L):
        self.typedef = typedef
        self.protocol = protocol


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens: List[Token] = tokens
        self.current = 0

    def parse(self):
        return self._protocol()

    def _protocol(self) -> Protocol:
        typedefs = []
        while True:
            try:
                typedefs.append(self._typedef())
            except:
                break

        protocol = None
        try:
            protocol = self._p()
        except:
            try:
                protocol = self._l()
            except:
                self._throw('P | L')

        return Protocol(typedefs, protocol)

    def _p(self) -> P:
        if not self._match(TokenType.GLOBAL):
            self._throw('global')

        if not self._match(TokenType.PROTOCOL):
            self._throw('protocol')

        protocol_name = self._identifier()

        if not self._match(TokenType.LEFT_PARENS):
            self._throw('(')

        roles = self._roles()

        if not self._match(TokenType.RIGHT_PARENS):
            self._throw(')')

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        g = []
        while True:
            try:
                g.append(self._g())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return P(protocol_name, roles, g)

    def _g(self) -> G:
        statement = None
        try:
            statement = self._global_interaction()
        except:
            try:
                statement = self._global_choice()
            except:
                try:
                    statement = self._global_recursion()
                except:
                    try:
                        statement = self._call()
                    except:
                        try:
                            statement = self._end()
                        except:
                            self._throw('global_interaction | global_choice | global_recursion | call | "End"')

        return G(statement)

    def _global_interaction(self) -> GlobalInteraction:
        message = self._message()

        if not self._match(TokenType.FROM):
            self._throw('from')

        sender = self._identifier()

        if not self._match(TokenType.TO):
            self._throw('to')

        recipient = self._identifier()

        if not self._match(TokenType.SEMICOLON):
            self._throw(';')

        return GlobalInteraction(message, sender, recipient)

    def _global_choice(self) -> GlobalChoice:
        if not self._match(TokenType.CHOICE):
            self._throw('choice')

        if not self._match(TokenType.FROM):
            self._throw('from')

        sender = self._identifier()

        if not self._match(TokenType.TO):
            self._throw('to')

        recipient = self._identifier()

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        g1 = []
        while True:
            try:
                g1.append(self._g())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        if not self._match(TokenType.OR):
            self._throw('or')

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        g2 = []
        while True:
            try:
                g2.append(self._g())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return GlobalChoice(sender, recipient, g1, g2)

    def _global_recursion(self) -> GlobalRecursion:
        if not self._match(TokenType.REC):
            self._throw('rec')

        identifier = self._identifier()

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        g: List[G] = []
        while True:
            try:
                g.append(self._g())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return GlobalRecursion(identifier, g)

    def _l(self) -> L:
        if not self._match(TokenType.LOCAL):
            self._throw('local')

        if not self._match(TokenType.PROTOCOL):
            self._throw('protocol')

        protocol_name = self._identifier()

        if not self._match(TokenType.AT):
            self._throw('at')

        perspective = self._identifier()

        if not self._match(TokenType.LEFT_PARENS):
            self._throw('(')

        roles = self._roles()

        if not self._match(TokenType.RIGHT_PARENS):
            self._throw(')')

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        t = []
        while True:
            try:
                t.append(self._t())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return L(protocol_name, perspective, roles, t)

    def _t(self) -> T:
        statement = None
        try:
            statement = self._local_send()
        except:
            try:
                statement = self._local_recv()
            except:
                try:
                    statement = self._local_choice()
                except:
                    try:
                        statement = self._local_recursion()
                    except:
                        try:
                            statement = self._call()
                        except:
                            try:
                                statement = self._end()
                            except:
                                self._throw('local_send | local_recv | local_choice | local_recursion | call | "end"')

        return T(statement)

    def _local_choice(self) -> LocalChoice:
        op = None

        try:
            if not self._match(TokenType.OFFER):
                self._throw('offer')

            if not self._match(TokenType.TO):
                self._throw('to')

            op = 'offer'
        except:
            try:
                if not self._match(TokenType.CHOICE):
                    self._throw('choice')

                if not self._match(TokenType.FROM):
                    self._throw('from')

                op = 'choice'
            except:
                self._throw('"offer" "to" | "choice" "from"')

        identifier = self._identifier()

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        t1 = []
        while True:
            try:
                t1.append(self._t())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        if not self._match(TokenType.OR):
            self._throw('or')

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        t2 = []
        while True:
            try:
                t2.append(self._t())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return LocalChoice(identifier, op, t1, t2)

    def _local_recursion(self) -> LocalRecursion:
        if not self._match(TokenType.REC):
            self._throw('rec')

        identifier = self._identifier()

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        t: List[T] = []
        while True:
            try:
                t.append(self._t())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return LocalRecursion(identifier, t)

    def _local_send(self) -> LocalSend:
        message = self._message()

        if not self._match(TokenType.TO):
            self._throw('to')

        identifier = self._identifier()

        if not self._match(TokenType.SEMICOLON):
            self._throw(';')

        return LocalSend(message, identifier)

    def _local_recv(self) -> LocalRecv:
        message = self._message()

        if not self._match(TokenType.FROM):
            self._throw('from')

        identifier = self._identifier()

        if not self._match(TokenType.SEMICOLON):
            self._throw(';')

        return LocalRecv(message, identifier)

    def _message(self) -> Message:
        label = self._identifier()

        if not self._match(TokenType.LEFT_PARENS):
            self._throw('(')

        payload = self._identifier()

        if not self._match(TokenType.RIGHT_PARENS):
            self._throw(')')

        return Message(label, payload)

    def _typedef(self) -> TypeDef:

        if not self._match(TokenType.TYPE):
            self._throw('type')

        if not self._match(TokenType.LT):
            self._throw('<')

        typ = self._identifier()

        if not self._match(TokenType.GT):
            self._throw('>')

        if not self._match(TokenType.AS):
            self._throw('as')

        identifier = self._identifier()

        if not self._match(TokenType.SEMICOLON):
            self._throw(';')

        return TypeDef(typ, identifier)

    def _roles(self) -> Roles:
        roles: List[Role] = [self._role()]

        while self._match(TokenType.COMMA):
            roles.append(self._role())

        return Roles(roles)

    def _role(self) -> Role:
        if not self._match(TokenType.ROLE):
            self._throw('role')

        identifier = self._identifier()
        return Role(identifier)

    def _identifier(self) -> Identifier:
        if self._match(TokenType.IDENTIFIER):
            return Identifier(self._previous().literal)
        self._throw('identifier')

    def _call(self) -> Call:
        if not self._match(TokenType.CONTINUE):
            self._throw('continue')

        identifier = self._identifier()

        if not self._match(TokenType.SEMICOLON):
            self._throw(';')

        return Call(identifier)

    def _end(self) -> End:
        if not self._match(TokenType.END):
            self._throw('End')

        if not self._match(TokenType.SEMICOLON):
            self._throw(';')

        return End()

    def _match(self, *types: TokenType) -> bool:
        for typ in types:
            if self._check(typ):
                self._advance()
                return True
        return False

    def _check(self, typ: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek() == typ

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current = self.current + 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek() == TokenType.EOF

    def _peek(self) -> TokenType:
        return self.tokens[self.current].typ

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _throw(self, typ: str):
        raise Exception(f"Expected '{typ}' => {self.tokens[self.current]} <= ")

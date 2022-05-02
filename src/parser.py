from lexer import Token, TokenType

from typing import List, Callable, Any

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


class ParseError(Exception):
    ...


class End:
    ...


class Identifier:
    def __init__(self, identifier: str):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier

    def __repr__(self):
        return self.visit()


class Call:
    def __init__(self, identifier: Identifier):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier.visit()

    def __repr__(self):
        return self.visit()


class Role:
    def __init__(self, identifier: Identifier):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier.visit()

    def __repr__(self):
        return self.visit()


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
        self.identifier = identifier
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
        typedefs = _many(self._typedef)
        protocol: P | L = self._or_else('P | L', self._p, self._l)

        return Protocol(typedefs, protocol)

    def _p(self) -> P:
        self._match(TokenType.GLOBAL, TokenType.PROTOCOL)

        protocol_name = self._identifier()

        self._match(TokenType.LEFT_PARENS)

        roles = self._roles()

        self._match(TokenType.RIGHT_PARENS, TokenType.LEFT_BRACE)

        g = _many(self._g)

        self._match(TokenType.RIGHT_BRACE)

        return P(protocol_name, roles, g)

    def _g(self) -> G:
        statement = self._or_else('global_interaction | global_choice | global_recursion | call | "End"',
                                  self._global_interaction, self._global_choice, self._global_recursion, self._call,
                                  self._end)

        return G(statement)

    def _global_interaction(self) -> GlobalInteraction:
        message = self._message()

        self._match(TokenType.FROM)

        sender = self._identifier()

        self._match(TokenType.TO)

        recipient = self._identifier()

        self._match(TokenType.SEMICOLON)

        return GlobalInteraction(message, sender, recipient)

    def _global_choice(self) -> GlobalChoice:
        self._match(TokenType.CHOICE, TokenType.FROM)

        sender = self._identifier()

        self._match(TokenType.TO)

        recipient = self._identifier()

        self._match(TokenType.LEFT_BRACE)

        g1 = _many(self._g)

        self._match(TokenType.RIGHT_BRACE, TokenType.OR, TokenType.LEFT_BRACE)

        g2 = _many(self._g)

        self._match(TokenType.RIGHT_BRACE)

        return GlobalChoice(sender, recipient, g1, g2)

    def _global_recursion(self) -> GlobalRecursion:
        self._match(TokenType.REC)

        identifier = self._identifier()

        self._match(TokenType.LEFT_BRACE)

        g = _many(self._g)

        self._match(TokenType.RIGHT_BRACE)

        return GlobalRecursion(identifier, g)

    def _l(self) -> L:
        self._match(TokenType.LOCAL, TokenType.PROTOCOL)

        protocol_name = self._identifier()

        self._match(TokenType.AT)

        perspective = self._identifier()

        self._match(TokenType.LEFT_PARENS)

        roles = self._roles()

        self._match(TokenType.RIGHT_PARENS, TokenType.LEFT_BRACE)

        t = _many(self._t)

        self._match(TokenType.RIGHT_BRACE)

        return L(protocol_name, perspective, roles, t)

    def _t(self) -> T:
        statement = self._or_else('local_send | local_recv | local_choice | local_recursion | call | "end"',
                                  self._local_send, self._local_recv, self._local_choice, self._local_recursion,
                                  self._call, self._end)

        return T(statement)

    def _local_choice(self) -> LocalChoice:
        def _offer_to() -> str:
            self._match(TokenType.OFFER, TokenType.TO)

            return 'offer'

        def _choice_from() -> str:
            self._match(TokenType.CHOICE, TokenType.FROM)

            return 'choice'

        op = self._or_else('"offer" "to" | "choice" "from"', _offer_to, _choice_from)

        identifier = self._identifier()

        self._match(TokenType.LEFT_BRACE)

        t1 = _many(self._t)

        self._match(TokenType.RIGHT_BRACE, TokenType.OR, TokenType.LEFT_BRACE)

        t2 = _many(self._t)

        self._match(TokenType.RIGHT_BRACE)

        return LocalChoice(identifier, op, t1, t2)

    def _local_recursion(self) -> LocalRecursion:
        self._match(TokenType.REC)

        identifier = self._identifier()

        self._match(TokenType.LEFT_BRACE)

        t = _many(self._t)

        self._match(TokenType.RIGHT_BRACE)

        return LocalRecursion(identifier, t)

    def _local_send(self) -> LocalSend:
        message = self._message()

        self._match(TokenType.TO)

        identifier = self._identifier()

        self._match(TokenType.SEMICOLON)

        return LocalSend(message, identifier)

    def _local_recv(self) -> LocalRecv:
        message = self._message()

        self._match(TokenType.FROM)

        identifier = self._identifier()

        self._match(TokenType.SEMICOLON)

        return LocalRecv(message, identifier)

    def _message(self) -> Message:
        label = self._identifier()

        self._match(TokenType.LEFT_PARENS)

        payload = self._identifier()

        self._match(TokenType.RIGHT_PARENS)

        return Message(label, payload)

    def _typedef(self) -> TypeDef:

        self._match(TokenType.TYPE, TokenType.LT)

        typ = self._identifier()

        self._match(TokenType.GT, TokenType.AS)

        identifier = self._identifier()

        self._match(TokenType.SEMICOLON)

        return TypeDef(typ, identifier)

    def _roles(self) -> Roles:
        roles: List[Role] = [self._role()]

        while self._matches(TokenType.COMMA):
            roles.append(self._role())

        return Roles(roles)

    def _role(self) -> Role:
        self._match(TokenType.ROLE)

        identifier = self._identifier()
        return Role(identifier)

    def _identifier(self) -> Identifier:
        self._match(TokenType.IDENTIFIER)

        return Identifier(self._previous().literal)

    def _call(self) -> Call:
        self._match(TokenType.CONTINUE)

        identifier = self._identifier()

        self._match(TokenType.SEMICOLON)

        return Call(identifier)

    def _end(self) -> End:
        self._match(TokenType.END, TokenType.SEMICOLON)

        return End()

    def _or_else(self, err: str, *rules: Callable) -> Any:
        for rule in rules:
            _token = self.current
            try:
                return rule()
            except ParseError:
                self.current = _token

        self._throw(err)

    def _matches(self, typ: TokenType) -> bool:
        if self._check(typ):
            self._advance()
            return True
        return False

    def _match(self, *types: TokenType) -> None:
        for typ in types:
            if not self._matches(typ):
                self._throw(str(typ))

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
        raise ParseError(f"Expected '{typ}' => {self.tokens[self.current]} <= ")


def _many(rule: Callable) -> List:
    matches = []

    while True:
        try:
            matches.append(rule())
        except ParseError:
            break

    return matches

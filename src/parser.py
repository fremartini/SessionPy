from lexer import Token, TokenType

from typing import List

"""
protocol        -> "global" "protocol" identifier "(" roles ")" "{" statement* "}";
statement       -> choice | action;
choice          -> "choice" "at" identifier "{" statement* "}" "or" "{" statement* "}";
action          -> (recurse | transmit) ";";
recurse         -> "do" identifier "(" roles ")";
transmit        -> primary "from" identifier ("to | "from") identifier;
roles           -> role ("," role)*;
role            -> "role" identifier;
identifier      -> [A-Z] ([A-Z] | [a-z] | 0 - 9)*;
primary         -> STR | INT | "BOOL;
"""


class Primary:
    def __init__(self, literal: type):
        self.literal = literal


class Identifier:
    def __init__(self, identifier: str):
        self.identifier = identifier


class Role:
    def __init__(self, identifier: Identifier):
        self.identifier = identifier


class Roles:
    def __init__(self, roles: List[Role]):
        self.roles = roles


class Transmit:
    def __init__(self, primary: Primary, identifier1: Identifier, identifier2: Identifier):
        self.primary = primary
        self.identifier1 = identifier1
        self.identifier2 = identifier2


class Recurse:
    def __init__(self, identifier: Identifier, roles: Roles):
        self.identifier = identifier
        self.roles = roles


class Action:
    def __init__(self, action: Recurse | Transmit):
        self.action = action


class Choice:
    def __init__(self, identifier: Identifier, statementsDO, statementsOR):
        self.identifier = identifier
        self.statementsDO = statementsDO
        self.statementsOR = statementsOR


class Statement:
    def __init__(self, statement: Choice | Action):
        self.statement = statement


class Protocol:
    def __init__(self, identifier: Identifier, roles: Roles, statements: List[Statement]):
        self.identifier = identifier
        self.roles = roles
        self.statements = statements


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens: List[Token] = tokens
        self.current = 0

    def parse(self):
        return self._protocol()

    def _protocol(self) -> Protocol:
        if not self._match(TokenType.GLOBAL):
            self._throw('global')

        if not self._match(TokenType.PROTOCOL):
            self._throw('protocol')

        identifier = self._identifier()

        if not self._match(TokenType.LEFT_PARENS):
            self._throw('(')

        roles = self._roles()

        if not self._match(TokenType.RIGHT_PARENS):
            self._throw(')')

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        statements: List[Statement] = []
        # self._statement()

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return Protocol(identifier, roles, statements)

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

    def _statement(self) -> Statement:
        ...

    def _primary(self) -> Primary:
        if self._match(TokenType.STR):
            return Primary(str)

        if self._match(TokenType.INT):
            return Primary(str)

        if self._match(TokenType.BOOL):
            return Primary(bool)

        self._throw('')

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

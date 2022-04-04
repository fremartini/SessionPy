from lexer import Token, TokenType

from typing import List

"""
protocol            -> typedef* (global_protocol | local_protocol);

global_protocol     -> "global" "protocol" identifier "(" roles ")" "{" global_statement* "}";
global_statement    -> global_choice | global_action | end;
global_choice       -> "choice" "from" identifier "to" identifier "{" global_statement* "}" "or" "{" global_statement* "}";
global_action       -> (recurse | global_transmit) ";";
global_transmit     -> identifier "from" identifier ("to | "from") identifier;

local_protocol      -> "local" "protocol" identifier "at" identifier "(" roles ")" "{" local_statement* "}";
local_statement     -> local_choice | local_action | end;
local_choice        -> ("offer" "to" | "choice" "from") identifier "{" local_statement* "}" "or" "{" local_statement* "}"
local_action        -> (recurse | local_transmit) ";";
local_transmit      -> identifier ("to | "from") identifier;

typedef             -> "type" "<" identifier ">" "as" identifier ";";
recurse             -> "do" identifier;
roles               -> role ("," role)*;
role                -> "role" identifier;
identifier          -> [A-Z] ([A-Z] | [a-z] | 0 - 9)*;
end                 -> "end";
"""


class Primary:
    def __init__(self, literal: type):
        self.literal = literal

    def visit(self) -> str:
        return str(self.literal)


class Identifier:
    def __init__(self, identifier: str):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier


class Role:
    def __init__(self, identifier: Identifier):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier.visit()


class Identifiers:
    def __init__(self, identifiers: List[Identifier]):
        self.identifiers = identifiers

    def visit(self) -> List[str]:
        return [i.visit() for i in self.identifiers]


class Roles:
    def __init__(self, roles: List[Role]):
        self.roles = roles

    def visit(self) -> List[str]:
        return [i.visit() for i in self.roles]


class Transmit:
    def __init__(self, primary: Primary, identifier1: Identifier, identifier2: Identifier):
        self.primary = primary
        self.identifier1 = identifier1
        self.identifier2 = identifier2


class Recurse:
    def __init__(self, identifier: Identifier):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier.visit()


class Action:
    def __init__(self, action: Recurse | Transmit):
        self.action = action

    def visit(self) -> str:
        return self.action.visit()


class Choice:
    def __init__(self, identifier: Identifier, statementsDO, statementsOR):
        self.identifier = identifier
        self.statementsDO = statementsDO
        self.statementsOR = statementsOR


class Statement:
    def __init__(self, statement: Choice | Action):
        self.statement = statement

    def visit(self) -> str:
        return self.statement.visit()


class Protocol:
    def __init__(self, identifier: Identifier, roles: Roles, statements: List[Statement]):
        self.identifier = identifier
        self.roles = roles
        self.statements = statements


class Projector:
    def project(self, root: Protocol):
        roles = root.roles.visit()
        for r in roles:
            role_str = ''.join([f'role {R}, ' for R in roles]).removesuffix(', ')
            with open(f'{r}.scr', "w") as f:
                f.write(f'local protocol {root.identifier.visit()} at {r} ({role_str})')
                f.writelines(self._project_local_protocol_for(r, root))

    def _project_local_protocol_for(self, role: str, root : Protocol) -> List[str]:
        actions = []
        for stmt in root.statements:
            actions.append(self._project_statement(role, stmt))
        return actions

    def _project_statement(self, role: str, s: Statement) -> str:
        match s.statement:
            case choice if isinstance(choice, Choice):
                ...
            case action if isinstance(action, Action):
                return self._project_action(role, action)

    def _project_action(self, role: str, a: Action) -> str:
        match a.action:
            case recurse if isinstance(recurse, Recurse):
                return f'jump {recurse.visit()}'
            case transmit if isinstance(transmit, Transmit):
                return self._project_transmit(role, transmit)

    def _project_transmit(self, role: str, t: Transmit) -> str:
        sender = t.identifier1.visit()
        receiver = t.identifier2.visit()
        message = t.primary.visit()
        if role == sender:
            return f'\n{message} to {receiver}'
        elif role == receiver:
            return f'\n{message} from {sender}'


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

        statements = []
        while True:
            try:
                statements.append(self._statement())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return Protocol(identifier, roles, statements)

    def _roles(self) -> Roles:
        roles: List[Role] = [self._role()]

        while self._match(TokenType.COMMA):
            roles.append(self._role())

        return Roles(roles)

    def _identifiers(self) -> Identifiers:
        identifiers: List[Identifier] = [self._identifier()]

        while self._match(TokenType.COMMA):
            identifiers.append(self._identifier())

        return Identifiers(identifiers)

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
        statement = None

        try:
            statement = self._choice()
        except:
            try:
                statement = self._action()
            except:
                self._throw('choice | action')

        return Statement(statement)

    def _choice(self) -> Choice:
        if not self._match(TokenType.CHOICE):
            self._throw('choice')

        if not self._match(TokenType.AT):
            self._throw('at')

        identifier = self._identifier()

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        statementsDO = []
        while True:
            try:
                statementsDO.append(self._statement())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        if not self._match(TokenType.OR):
            self._throw('or')

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        statementsOR = []
        while True:
            try:
                statementsOR.append(self._statement())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return Choice(identifier, statementsDO, statementsOR)

    def _action(self) -> Action:
        action = None
        try:
            action = self._recurse()
        except:
            try:
                action = self._transmit()
            except:
                self._throw('recurse | transmit')

        self._match(TokenType.SEMICOLON)

        return Action(action)

    def _recurse(self) -> Recurse:
        if not self._match(TokenType.DO):
            self._throw('do')

        identifier = self._identifier()

        return Recurse(identifier)

    def _transmit(self) -> Transmit:
        primary = self._primary()

        if not self._match(TokenType.FROM):
            self._throw('from')

        identifier1 = self._identifier()

        if not self._match(TokenType.TO, TokenType.FROM):
            self._throw('to, from')

        identifier2 = self._identifier()

        return Transmit(primary, identifier1, identifier2)

    def _primary(self) -> Primary:
        if self._match(TokenType.STR):
            return Primary(str)

        if self._match(TokenType.INT):
            return Primary(int)

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

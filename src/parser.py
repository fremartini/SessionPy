from lexer import Token, TokenType

from typing import List

"""
protocol            -> typedef* (global_protocol | local_protocol);

global_protocol     -> "global" "protocol" identifier "(" roles ")" "{" global_statement* "}";
global_statement    -> global_choice | global_action | end;
global_choice       -> "choice" "from" identifier "to" identifier "{" global_statement* "}" "or" "{" global_statement* "}";
global_action       -> (recurse | global_transmit) ";";
global_transmit     -> message "from" identifier ("to | "from") identifier;

local_protocol      -> "local" "protocol" identifier "at" identifier "(" roles ")" "{" local_statement* "}";
local_statement     -> local_choice | local_action | end;
local_choice        -> ("offer" "to" | "choice" "from") identifier "{" local_statement* "}" "or" "{" local_statement* "}"
local_action        -> (recurse | local_transmit) ";";
local_transmit      -> message ("to | "from") identifier;

message             -> identifier "(" identifier ")";
typedef             -> "type" "<" identifier ">" "as" identifier ";";
recurse             -> "do" identifier;
roles               -> role ("," role)*;
role                -> "role" identifier;
identifier          -> [A-Z] ([A-Z] | [a-z] | 0 - 9)*;
end                 -> "end";
"""


class End:
    ...


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


class Roles:
    def __init__(self, roles: List[Role]):
        self.roles = roles

    def visit(self) -> List[str]:
        return [i.visit() for i in self.roles]


class Recurse:
    def __init__(self, identifier: Identifier):
        self.identifier = identifier

    def visit(self) -> str:
        return self.identifier.visit()


class TypeDef:
    def __init__(self, typ: Identifier, identifier: Identifier):
        self.typ = typ
        self.identifier = identifier


class Message:
    def __init__(self, label: Identifier, payload: Identifier):
        self.label = label
        self.payload = payload


class LocalTransmit:
    def __init__(self, message: Message, identifier: Identifier):
        self.message = message
        self.identifier = identifier


class LocalAction:
    def __init__(self, action: Recurse | LocalTransmit):
        self.action = action


class LocalChoice:
    def __init__(self, identifier: Identifier, statementsDO, statementsOR):
        self.identifier = identifier
        self.statementsDO = statementsDO
        self.statementsOR = statementsOR


class LocalStatement:
    def __init__(self, statement: LocalChoice | LocalAction | End):
        self.statement = statement


class LocalProtocol:
    def __init__(self, protocol_name: Identifier, perspective: Identifier, roles: Roles,
                 statements: List[LocalStatement]):
        self.protocol_name = protocol_name
        self.perspective = perspective
        self.roles = roles
        self.statements = statements


class GlobalTransmit:
    def __init__(self, message: Message, sender: Identifier, recipient: Identifier):
        self.message = message
        self.sender = sender
        self.recipient = recipient


class GlobalAction:
    def __init__(self, action: Recurse | GlobalTransmit):
        self.action = action


class GlobalChoice:
    def __init__(self, sender: Identifier, recipient: Identifier, statementsDO, statementsOR):
        self.sender = sender
        self.recipient = recipient
        self.statementsDO = statementsDO
        self.statementsOR = statementsOR


class GlobalStatement:
    def __init__(self, statement: GlobalChoice | GlobalAction | End):
        self.statement = statement


class GlobalProtocol:
    def __init__(self, protocol_name: Identifier, roles: Roles, statements: List[GlobalStatement]):
        self.protocol_name = protocol_name
        self.roles = roles
        self.statements = statements


class Protocol:
    def __init__(self, typedef: List[TypeDef], protocol: GlobalProtocol | LocalProtocol):
        self.typedef = typedef
        self.protocol: protocol


"""
class Projector:
    def project(self, root: Protocol):
        roles = root.roles.visit()
        for r in roles:
            role_str = ''.join([f'role {R}, ' for R in roles]).removesuffix(', ')
            with open(f'{r}.scr', "w") as f:
                f.write(f'local protocol {root.identifier.visit()} at {r} ({role_str})')
                f.writelines(self._project_local_protocol_for(r, root))

    def _project_local_protocol_for(self, role: str, root: Protocol) -> List[str]:
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
"""


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
            protocol = self._global_protocol()
        except:
            try:
                protocol = self._local_protocol()
            except:
                self._throw('global_protocol | local_protocol')

        return Protocol(typedefs, protocol)


    def _global_protocol(self) -> GlobalProtocol:
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

        statements = []
        while True:
            try:
                statements.append(self._global_statement())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return GlobalProtocol(protocol_name, roles, statements)

    def _global_statement(self) -> GlobalStatement:
        statement = None
        try:
            statement = self._global_choice()
        except:
            try:
                statement = self._global_action()
            except:
                try:
                    statement = self._end()
                except:
                    self._throw('global_choice | global_action | end')

        return GlobalStatement(statement)

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

        statementsDO = []
        while True:
            try:
                statementsDO.append(self._global_statement())
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
                statementsOR.append(self._global_statement())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return GlobalChoice(sender, recipient)

    def _global_action(self) -> GlobalAction:
        action = None
        try:
            action = self._recurse()
        except:
            try:
                action = self._global_transmit()
            except:
                self._throw('recurse | global_transmit')

        if not self._match(TokenType.SEMICOLON):
            self._throw(';')

        return GlobalAction(action)

    def _global_transmit(self) -> GlobalTransmit:
        message = self._message()

        if not self._match(TokenType.FROM):
            self._throw('from')

        sender = self._identifier()

        try:
            if not self._match(TokenType.TO):
                self._throw('to')
        except:
            try:
                if not self._match(TokenType.FROM):
                    self._throw('from')
            except:
                self._throw('"to" | "from"')

        recipient = self._identifier()

        return GlobalTransmit(message, sender, recipient)



    def _local_protocol(self) -> LocalProtocol:
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

        statements = []
        while True:
            try:
                statements.append(self._local_statement())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return LocalProtocol(protocol_name, perspective, roles, statements)

    def _local_statement(self) -> LocalStatement:
        statement = None
        try:
            statement = self._local_choice()
        except:
            try:
                statement = self._local_action()
            except:
                try:
                    statement = self._end()
                except:
                    self._throw('local_choice | local_action | end')

        return LocalStatement(statement)


    def _local_choice(self) -> LocalChoice:
        try:
            if not self._match(TokenType.OFFER):
                self._throw('offer')

            if not self._match(TokenType.TO):
                self._throw('to')
        except:
            try:
                if not self._match(TokenType.CHOICE):
                    self._throw('offer')

                if not self._match(TokenType.FROM):
                    self._throw('to')
            except:
                self._throw('"offer" "to" | "choice" "from"')

        identifier = self._identifier()

        if not self._match(TokenType.LEFT_BRACE):
            self._throw('{')

        statementsDO = []
        while True:
            try:
                statementsDO.append(self._local_statement())
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
                statementsOR.append(self._local_statement())
            except:
                break

        if not self._match(TokenType.RIGHT_BRACE):
            self._throw('}')

        return LocalChoice(identifier, statementsDO, statementsOR)


    def _local_action(self) -> LocalAction:
        action = None
        try:
            action = self._recurse()
        except:
            try:
                action = self._local_transmit()
            except:
                self._throw('recurse | local_transmit')

        if not self._match(TokenType.SEMICOLON):
            self._throw(';')

        return LocalAction(action)

    def _local_transmit(self) -> LocalTransmit:
        message = self._message()

        try:
            if not self._match(TokenType.TO):
                self._throw('to')
        except:
            try:
                if not self._match(TokenType.FROM):
                    self._throw('from')
            except:
                self._throw('"to" | "from"')

        identifier = self._identifier()

        return LocalTransmit(message, identifier)

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

    def _recurse(self) -> Recurse:
        if not self._match(TokenType.DO):
            self._throw('do')

        identifier = self._identifier()

        return Recurse(identifier)

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

    def _end(self) -> End:
        if self._match(TokenType.END):
            return End()

        self._throw('end')

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

from enum import Enum, auto
from typing import List

from lib import read_src_from_file


class TokenType(Enum):
    # single character tokens
    LEFT_PARENS = auto(),
    RIGHT_PARENS = auto(),
    LEFT_BRACE = auto(),
    RIGHT_BRACE = auto(),
    SEMICOLON = auto(),
    EOF = auto(),
    COMMA = auto(),
    LT = auto(),
    GT = auto(),
    AT_SIGN = auto(),

    # keywords
    GLOBAL = auto(),
    LOCAL = auto(),
    PROTOCOL = auto(),
    ROLE = auto(),
    FROM = auto(),
    TO = auto()
    CHOICE = auto(),
    OFFER = auto(),
    AS = auto(),
    AT = auto(),
    OR = auto(),
    END = auto(),
    TYPE = auto(),
    REC = auto(),
    CONTINUE = auto(),

    # types
    IDENTIFIER = auto(),


keywords = {
    "global": TokenType.GLOBAL,
    "local": TokenType.LOCAL,
    "protocol": TokenType.PROTOCOL,
    "role": TokenType.ROLE,
    "from": TokenType.FROM,
    "to": TokenType.TO,
    "choice": TokenType.CHOICE,
    "offer": TokenType.OFFER,
    "as": TokenType.AS,
    "at": TokenType.AT,
    "or": TokenType.OR,
    "End": TokenType.END,
    "type": TokenType.TYPE,
    "rec": TokenType.REC,
    "continue": TokenType.CONTINUE,
}


class Token:
    def __init__(self, typ: TokenType, literal: str | None):
        self.typ = typ
        self.literal = literal

    def __repr__(self) -> str:
        return f'({self.typ}, {self.literal})'


class Lexer:
    def __init__(self, file):
        self.source = read_src_from_file(file)
        self.start = 0
        self.current = 0
        self.tokens = []

    def lex(self) -> List[Token]:
        self._scan_tokens()
        return self.tokens

    def _scan_tokens(self) -> None:
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()

        self._add_token(TokenType.EOF)

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _scan_token(self) -> None:
        c = self._advance()
        match c:
            case '(':
                self._add_token(TokenType.LEFT_PARENS)
            case ')':
                self._add_token(TokenType.RIGHT_PARENS)
            case '{':
                self._add_token(TokenType.LEFT_BRACE)
            case '}':
                self._add_token(TokenType.RIGHT_BRACE)
            case ';':
                self._add_token(TokenType.SEMICOLON)
            case ',':
                self._add_token(TokenType.COMMA)
            case '<':
                self._add_token(TokenType.LT)
            case '>':
                self._add_token(TokenType.GT)
            case '@':
                self._add_token(TokenType.AT_SIGN)
            case x if x in [' ', '\r', '\t', '\n']:
                return
            case x:
                if c.isalpha():
                    self._identifier()
                else:
                    raise Exception(f'Unexpected character \'{x}\'')

    def _is_alphanumeric(self, c: str) -> bool:
        return c.isalpha() or c.isdigit()

    def _peek(self):
        if self._is_at_end():
            return '\0'
        return self.source[self.current]

    def _identifier(self) -> None:
        while self._is_alphanumeric(self._peek()):
            self._advance()

        text: str = self.source[self.start:self.current]
        typ: TokenType = TokenType.IDENTIFIER
        if text in keywords:
            self._add_token(keywords[text])
        else:
            self._add_token_literal(typ, text)

    def _advance(self) -> str:
        c = self.source[self.current]
        self.current = self.current + 1
        return c

    def _add_token(self, typ: TokenType) -> None:
        self.tokens.append(Token(typ, None))

    def _add_token_literal(self, typ: TokenType, literal: str) -> None:
        self.tokens.append(Token(typ, literal))

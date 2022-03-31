from lexer import Token
from typing import List

"""
protocol        -> "global" "protocol" identifier "(" parameters ")" "{" statement* "}"
parameters      -> role ("," role)*
statement       -> choice | action
choice          -> "choice" "at" identifier "{" statement* "}" "or" "{" statement* "}"
action          -> (recurse | transmit) ";";
recurse         -> "do" identifier "(" parameters* ")";
transmit        -> primary "from" identifier ("to | "from") identifier;
role            -> "role" identifier;
identifier      -> [A-Z] ([A-Z] | [a-z] | 0 - 9)*
primary         -> "str" | "int" | "bool";
"""


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens: List[Token] = tokens
        self.current = 0

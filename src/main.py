from typing import *

from lexer import Lexer
from parser import Parser
from projector import Projector


def run(file: str) -> List[str] | str:
    tokens = Lexer(file).lex()
    ast = Parser(tokens).parse()
    return Projector().project(ast)


files = run('../programs/Stream.scr')
for f in files:
    run(f)

from typing import *

from lexer import Lexer
from parser import Parser
from projector import Projector


def run(file: str) -> List[str] | str:
    tokens = Lexer(file).lex()
    ast = Parser(tokens).parse()
    return Projector().project(ast)

def run_many(*files: str):
    for file in files:
        run(file)


run_many('../programs/RepeatingConversation_Alice.scr', '../programs/RepeatingConversation_Bob.scr')

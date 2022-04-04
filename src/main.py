from lexer import Lexer
from parser import Parser, Projector

if __name__ == '__main__':
    tokens = Lexer('../programs/Alice.scr').lex()
    tree = Parser(tokens).parse()
    Projector().project(tree)

from lexer import Lexer
from parser import Parser

if __name__ == '__main__':
    tokens = Lexer('protocol.scr').lex()

    for t in tokens:
        print(t)

    tree = Parser(tokens).parse()
    print(tree)

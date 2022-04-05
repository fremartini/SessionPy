from lexer import Lexer
from parser import Parser

if __name__ == '__main__':
    tokens = Lexer('../programs/two_buyers.scr').lex()
    tree = Parser(tokens).parse()
    print(tree)
    #Projector().project(tree)

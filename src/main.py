from lexer import Lexer
from parser import Parser
from projector import Projector

tok = Lexer('B1.scr').lex()
ast = Parser(tok).parse()
Projector().project(ast)

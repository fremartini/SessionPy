from lexer import Lexer
from parser import Parser
from projector import Projector

tok = Lexer('../programs/two_buyers.scr').lex()
ast = Parser(tok).parse()
Projector().project(ast)
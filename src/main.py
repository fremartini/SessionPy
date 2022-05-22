import os
from typing import *

from lexer import Lexer
from parser import Parser
from projector import Projector
from immutable_list import ImmutableList


def project_file(file: str) -> List[str] | str:
    tokens = Lexer(file).lex()
    ast = Parser(tokens).parse()
    return Projector().project(ast)


def project_many(*files: str):
    for file in files:
        project_file(file)


def project_global_protocol(file: str):
    local_protocols = project_file(file)
    for p in local_protocols:
        project_file(p)


def project_all_global_protocols():
    all_files = ImmutableList(os.listdir('../programs'))
    global_protocols = all_files.filter(
        lambda file: file.endswith('.scr') and '_' not in file)

    global_protocols.map(lambda file: project_global_protocol(f'../programs/{file}'))


# project_all_global_protocols()
project_global_protocol('../programs/TwoBuyers.scr')
# project_many('../programs/RepeatingConversation_Alice.scr', '../programs/RepeatingConversation_Bob.scr')

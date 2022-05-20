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


def project_global_protocol(file: str):
    local_protocols = project_file(file)
    for p in local_protocols:
        project_file(p)


def project_all_global_protocols():
    all_files = ImmutableList(os.listdir('../programs'))
    global_protocols = all_files.filter(
        lambda file: file.endswith('.scr') and '_' not in file)

    for gb in global_protocols:
        local_protocols = project_file(f'../programs/{gb}')
        for lp in local_protocols:
            project_file(lp)

#project_all_global_protocols()
project_global_protocol('../programs/TwoBuyers.scr')

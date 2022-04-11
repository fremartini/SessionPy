import os
import sys
import unittest
import inspect
import ast
from textwrap import dedent

def get_ast(f) -> ast.Module:
    return ast.parse(dedent(inspect.getsource(f)))


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.context import *
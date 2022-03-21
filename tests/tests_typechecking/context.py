import os
import unittest
import sys
import ast
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.context import *

def get_ast(f) -> ast.Module:
    return ast.parse(dedent(inspect.getsource(f)))
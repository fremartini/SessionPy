import os
import unittest
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.context import *
from textwrap import dedent
import inspect


def get_ast(f) -> ast.Module:
    return ast.parse(dedent(inspect.getsource(f)))

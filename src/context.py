import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from debug import *
from lib import *
from check import *
import inspect
from textwrap import dedent
def get_ast(f) -> ast.Module:
    return ast.parse(dedent(inspect.getsource(f)))

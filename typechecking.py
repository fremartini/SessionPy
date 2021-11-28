import inspect
import ast
from pprint import pprint
from scanner import Scanner
from textwrap import dedent
from checker import Checker

"""
Annotate functions that should have its channels checked, with this decorator
"""
def verify_channels(f):
    analyzer = Analyzer(f)
    analyzer.scan()
    analyzer.check()
    return f

class Analyzer():
    def __init__(self, func):
        self.func = func

    """
    Scan the file the decorated function belongs to, for functions
    that has Channels as parameters
    """
    def scan(self):
        file = dedent(inspect.getfile(self.func))
        src = self._read_src_from_file(file)
        tree : ast.Module = ast.parse(src)
        self.functions, self.channels = Scanner(tree).run()

    """
    Check that Channels are used correctly in all functions which they are used
    """
    def check(self):
        src = dedent(inspect.getsource(self.func))
        tree = ast.parse(src)
        Checker(tree, self.functions, self.channels).run()
           
    def report(self):
        pprint(self.channels)

    def _read_src_from_file(self, file):
        with open(file, "r") as f:
            return f.read()
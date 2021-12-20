import inspect
import ast
from scanner import Scanner
from textwrap import dedent
from checker import Checker
from util import channels_str

"""
Annotate functions that should have its channels checked with this decorator
"""
def verify_channels(f):
    functions, channels = scan(f)
    if (functions or channels):
        check(f, functions, channels)
    return f

"""
Scan the file the decorated function belongs to, for functions
that has Channels as parameters
"""
def scan(func):
    file = dedent(inspect.getfile(func))
    file_src = _read_src_from_file(file)
    file_ast = ast.parse(file_src)
    tree = ast.parse(dedent(inspect.getsource(func)))
    functions, channels = Scanner(tree, file_ast).run()
    #print(f"#####\nScanner phase found:\nfunctions: {functions}\nchannels: {channels_str(channels)}#####")
    return (functions, channels)

"""
Check that Channels are used correctly in all functions which they are used
"""
def check(func, functions, channels):
    src = dedent(inspect.getsource(func))
    tree = ast.parse(src)
    Checker(tree, functions, channels).run()
        
def _read_src_from_file(file):
    with open(file, "r") as f:
        return f.read()

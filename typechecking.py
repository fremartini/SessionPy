import inspect
import ast
from scanner import Scanner
from textwrap import dedent
from checker import Checker
from util import channels_str, dump_ast

def verify_channels(f):
    """annotate functions that should have its channels checked with this decorator"""
    functions, channels = scan(f)
    if channels:
        check(f, functions, channels)
    return f


def scan(func):
    """Scan the file the decorated function belongs to, for functions that has Channels as parameters"""
    func_src = dedent(inspect.getsource(func))
    func_ast = ast.parse(func_src)
    functions, channels = Scanner(func_ast).run()
    #print(f"#####\nScanner phase found:\nfunctions: {functions}\nchannels: {channels_str(channels)}#####")
    return (functions, channels)


def check(func, functions, channels):
    """Check that Channels are used correctly in all functions which they are used"""
    src = dedent(inspect.getsource(func))
    tree = ast.parse(src)
    Checker(tree, functions, channels).run()


def _read_src_from_file(file):
    with open(file, "r") as f:
        return f.read()

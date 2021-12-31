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
    """Scan the decorated function, for channel assignments and functions that has Channels as parameters"""
    func_src = dedent(inspect.getsource(func))
    func_ast = ast.parse(func_src)
    functions, channels = Scanner(func_ast).run()
    #print(f"#####\nScanner phase found:\nfunctions: {functions}\nchannels: {channels_str(channels)}#####")
    return (functions, channels)


def check(func, functions, channels):
    """Check that Channels are used correctly in all functions in which they are used"""
    func_src = dedent(inspect.getsource(func))
    func_ast = ast.parse(func_src)
    Checker(func_ast, functions, channels).run()
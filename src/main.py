from check import typecheck_file
from sessiontype import *
from channel import Channel
from typing import *

typecheck_file()

def f(n, m) -> str:
    if n == 0:
        return "hi"
    else:
        return "hello" + f(n-1, "ignored")

f(100, "ok")
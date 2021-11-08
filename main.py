from typeChecking import *

@checkReturnType
def inc(x: int) -> int:
    return x + 1
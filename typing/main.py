from check import check

# globals [test_binop -> float]
@check #hook into the pre-run phase. Can do better?
def test_binop(x : int, y : str) -> str:
    y : float = 1.0     # [x -> int]
    z : int = 100       # [x -> int, y -> float]
    n = 0

    w = (x + y) + z    # [x -> int, y -> float, z -> int]
                        # [x -> int, y -> float, z -> int, w -> float]
    return w

k = 1
test_binop(k, 1)
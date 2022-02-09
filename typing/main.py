from check import check

@check #hook into the pre-run phase. Can do better?
def test_binop():
    x : int = 41        # []
    y : float = 1.0     # [x -> int]
    z : int = 100       # [x -> int, y -> float]
    w = (x + y) + z     # [x -> int, y -> float, z -> int]
                        # [x -> int, y -> float, z -> int, w -> float]
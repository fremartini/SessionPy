from check import check

@check #hook into the pre-run phase. Can do better?
def add1(x : int):
    return x + 1

class A:
    pass

a : A = A()
#should fail
add1(a)
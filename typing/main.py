from check import check

@check #hook into the pre-run phase. Can do better?
def add1(x):
    y = 1

class A:
    ...

a = A()
k : int = 5
#should fail
add1(a)
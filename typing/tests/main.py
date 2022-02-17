from check import check

@check
def add1(x):
    return x + 1

class A:
    ...

a = A()
add1(a)
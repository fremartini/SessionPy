def fib(n) -> int:
    if n == 0:
        return 0
    elif n == 1 or n == 2:
        return 1

    else:
        return fib(n - 1) + fib(n - 2)


class A:

    def f(self):
        return 42


a = A()
a.f()
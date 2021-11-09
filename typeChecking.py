import inspect
from infer import *

def info(func):
    print("\nProperties of function '" + func.__name__ + "'")
    ann = func.__annotations__
    print("annotations " + str(ann) + "\n\nparameters")

    for i in inspect.signature(func).parameters:       
        print(i + " " + str(ann[i]) if (i in ann) else "Any")

    print("\nreturns " + (str(inspect.signature(func).return_annotation) if ('return' in ann) else "None"))
    return func

def typeCheck(func):
    ann = func.__annotations__
    assertEq(ann['return'], infer(func))

    def g(*xs):
        ann.pop('return', None)
        tps = zip(ann.values(), xs)
        
        for (t1,t2) in tps:
            assertEq(t1, type(t2))

    return g

def assertEq(expected, actual):
    if (not expected == actual):
        raise Exception("expected return type of " + str(expected) + ", found " + str(actual))

import inspect
from infer import infer

def info(func):
    print("\nProperties of function '" + func.__name__ + "'")
    ann = func.__annotations__
    print("annotations " + str(ann) + "\n\nparameters")

    for i in inspect.signature(func).parameters:       
        print(i + " " + str(ann[i]) if (i in ann) else "Any")

    print("\nreturns " + (str(inspect.signature(func).return_annotation) if ('return' in ann) else "None"))
    return func

def typeCheck(f):
    anno = f.__annotations__
    retType = anno['return']
    def g(*xs):
        anno.pop('return', None)
        tps = zip(anno.values(), xs)
        
        for (t1,t2) in tps:
            assert(t1 == type(t2))
        assert(type(f(*xs)) == retType)
    return g

def checkReturnType(func):
    assertEq(func.__annotations__['return'], infer(func))
    return func

def assertEq(expected, actual):
    if (not expected == actual):
        raise Exception("expected return type of " + str(expected) + ", found " + str(actual))

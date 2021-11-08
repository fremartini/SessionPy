import inspect
import infer
import typing #what to do with this?

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
    assert(infer(str(func)) == func.__annotations__['return'])
    return func
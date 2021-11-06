import inspect

def check(func):
    ann = func.__annotations__
    print(ann['a'])
    result = func(ann['a'])
    resultType = type(result)
    returnType = type(ann['return'])
    
    print(resultType)
    print(returnType)


    return func
    
def info(func):
    print("\nProperties of function '" + func.__name__ + "'")
    ann = func.__annotations__
    print("annotations " + str(ann) + "\n\nparameters")

    for i in inspect.signature(func).parameters:       
        print(i + " " + str(ann[i]) if (i in ann) else "Any")

    print("\nreturns " + (str(inspect.signature(func).return_annotation) if ('return' in ann) else "None"))
    return func
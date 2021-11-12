import inspect
import textwrap
import infer
import ast

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

    if 'return' in ann:
        assertEq(ann['return'], infer(func))
        
    def g(*xs):
        ann.pop('return', None)
        tps = zip(ann.values(), xs)
        
        for (t1,t2) in tps:
            assertEq(t1, type(t2))
    return g

def _top(m : ast.Module, kwargs):
    for b in m.body: _functionDef(b, kwargs)

def _functionDef(f : ast.FunctionDef, kwargs):
    for b in f.body: _expr(b, kwargs)

def _expr(e : ast.Expr, kwargs):
    _call(e.value, kwargs)

def _call(c : ast.Call, kwargs):
    name = _attribute(c.func)
    arg = _constant(c.args[0])

    if name in kwargs:
        exp = kwargs.get(name)
        act = type(arg)
        assertEq(exp, act)

def _attribute(a : ast.Attribute):
    return _name(a.value)

def _name(n : ast.Name):
    return n.id

def _constant(c : ast.Constant):
    return c.value

def check_channels(kwargs):
    def g(f):
        src = textwrap.dedent(inspect.getsource(f))
        tree = ast.parse(src)
        _top(tree, kwargs)
        return f
    return g

def _read_src_from_file(file):
    f = open(file, "r") 
    src = f.read()
    f.close()

    return src

def check_file(f):
    file = inspect.getfile(f)
    src = _read_src_from_file(file)

    tree : ast.Module = ast.parse(src)
    print(ast.dump(tree, indent=4))
    return f

def assertEq(expected, actual):
    if (not expected == actual):
        raise Exception("expected return type of " + str(expected) + ", found " + str(actual))

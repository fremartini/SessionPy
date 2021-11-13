import inspect
import textwrap
from typing import Any
from infer import infer, printAST, unknown
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

def check_file(f):
    file = inspect.getfile(f)
    src = _read_src_from_file(file)

    tree : ast.Module = ast.parse(src)
    return f

def check_channels(f):
    src = textwrap.dedent(inspect.getsource(f))
    tree = ast.parse(src)
    channels, exprs = _getChannelAssignments(tree)

    for k, v in exprs.items():
        if (v == Any):
            continue
        assertEq(channels[k], v)

    return f

def _getChannelAssignments(m : ast.Module):
    return _functionDef(m.body[0])

def _functionDef(f : ast.FunctionDef):
    assignments = dict()
    exprs = dict()

    for b in f.body: 
        typ = type(b)

        if (typ == ast.Assign):
            chName, chTyp = _assign(b)
            assignments[chName] = chTyp
        elif (typ == ast.Expr):
            chName, chTyp = _expr(b)
            exprs[chName] = chTyp
        else:
            unknown(b)

    return (assignments, exprs)

def _assign(a : ast.Assign):
    target = _name(a.targets[0])
    val = _assignCall(a.value)
    return (target, val)

def _expr(e : ast.Expr):
    return _exprCall(e.value)

def _exprCall(c : ast.Call):
    varName, op = _attribute(c.func)
    args = Any
    if (op == "send"):
        a = c.args[0]
        if (type(a) == ast.Constant):
            args = type(_constant(c.args[0]))
        elif (type(a) == ast.Name):
            args = type(_name(c.args[0]))
        else:
            unknown(a)

    return (varName, args)

def _constant(c : ast.Constant):
    return c.value

def _attribute(a : ast.Attribute):
    return (_name(a.value), a.attr)

def _assignCall(c : ast.Call):
    typ = _name(c.args[0])

    if (typ == 'str'):
        return str
    elif (typ == 'int'):
        return int
    elif (typ == 'bool'):
        return bool
    else: 
        unknown(typ)

def _name(n : ast.Name):
    return n.id

def _read_src_from_file(file):
    f = open(file, "r") 
    src = f.read()
    f.close()

    return src

def assertEq(expected, actual):
    if (not expected == actual):
        raise Exception("expected type " + str(expected) + ", found " + str(actual))

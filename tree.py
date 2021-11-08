from ast import *
    
#https://docs.python.org/3/library/ast.html

environment = {}

def infer(prog : str) -> None:
    tree = parse(prog)
    typ = _mod(tree)
    print("program returns type " + str(typ))
        
def _mod(prog):
    t = type(prog)

    if (t == Module):
        return _stmt(prog.body[0])
    else:
        _unknown(prog)

def _stmt(s):
    t = type(s)
    
    if (t == Expr):
        e : expr = s
        _expression(e)
    elif (t == Return):
        r : Return = s
        return _expr(r.value)
    elif (t == Assign):
        a : Assign = s
        return _assign(a)
    else:
        _unknown(s)

def _expr(e) -> type:
    t = type(e)

    if (t == Constant):
        return _constant(e)
    elif (t == Name):
        return _name(e)
    else:
        _unknown(e)

def _assign(a : Assign) -> type:
    for target in a.targets:
        n : Name = target
        environment[n.id] = _evalConstant(a.value)

    print(environment)

def _evalConstant(c: Constant) -> int:
    return c.value

def _constant(_: Constant) -> type:
    return int

def _name(n: Name) -> type:
    print("found " + str(type(environment[n.id])))
    return type(environment[n.id])

def _expression(e : Expr) -> type:
    return _expr(e.value)
    
def _unknown(u):
    raise Exception("Unknown type: " + str(type(u)))
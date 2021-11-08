from ast import *
    
#https://docs.python.org/3/library/ast.html

environment = {}
printAST = True

def infer(prog : str) -> type:
    tree = parse(prog)
    if (printAST):
        for i in tree.body:
            print(i)
    return _mod(tree)
     
def _mod(prog):
    t = type(prog)

    if (t == Module):
        for i in range(len(prog.body) -1):
            _stmt(prog.body[i]
        )
        return _stmt(prog.body[len(prog.body) -1])
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
    elif (t == FunctionDef):
        f : FunctionDef = s
        return _functionDef(f)
    else:
        _unknown(s)

def _expr(e) -> type:
    t = type(e)

    if (t == Constant):
        return _constant(e)
    elif (t == Name):
        return _name(e)
    elif (t == BinOp):
        pass
    else:
        _unknown(e)

def _functionDef(f: FunctionDef) -> type:
    for stmt in f.body:
        _stmt(stmt)

    _expr(f.returns)

def _assign(a : Assign) -> type:
    for target in a.targets:
        environment[target.id] = _evalConstant(a.value)

def _evalConstant(c: Constant) -> int:
    return c.value

def _constant(_: Constant) -> type:
    return int

def _name(n: Name) -> type:
    if n.id in environment:
        return type(environment[n.id])
    else:
        raise KeyError(n.id + " is not bound")

def _expression(e : Expr) -> type:
    return _expr(e.value)
    
def _collectReturnStatements(statements):
    returns = []

    for stmt in statements:
        if (type(stmt) == Return): returns.append(stmt)

    return returns

def _unknown(u):
    raise Exception("Unknown type: " + str(type(u)))
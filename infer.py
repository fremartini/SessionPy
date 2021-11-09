from ast import *
import inspect
    
#https://docs.python.org/3/library/ast.html

environment = {}
printAST = False

def infer(prog) -> type:
    tree = parse(inspect.getsource(prog))
    return inferFromAST(tree)

def inferFromAST(ast) -> type:
    if (printAST):
        print(dump(ast, indent=4))

    typ = _mod(ast)
    return typ
     
def _mod(prog):
    t = type(prog)

    if (t == Module):
        body = prog.body

        for i in range(len(body) -1):
            _stmt(body[i]
        )
        return _stmt(body[len(body) -1])
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
    _arguments(f.args)

    body = f.body

    for i in range(len(body) -1):
        _stmt(body[i]
    )

    return _stmt(body[len(body) -1])

def _arguments(a : arguments):
    for arg in a.args:
        _arg(arg)

def _arg(a: arg):
    environment[a.arg] = a.annotation.id

def _assign(a : Assign) -> type:
    for target in a.targets:
        environment[target.id] = _evalConstant(a.value)

def _evalConstant(c: Constant) -> int:
    return c.value

def _constant(c: Constant) -> type:
    return type(c.value)

def _name(n: Name) -> type:
    if n.id in environment:
        return environment[n.id]

def _expression(e : Expr) -> type:
    return _expr(e.value)

def _unknown(u):
    raise Exception("Unknown type: " + str(type(u)))
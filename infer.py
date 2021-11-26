from ast import *
import inspect
import textwrap
    
#https://docs.python.org/3/library/ast.html

_environment = {}
_print_ast = False

def print_ast(ast):
    print(dump(ast, indent=4))

def infer(expr) -> type:
    return type(expr)
    src = textwrap.dedent(inspect.getsource(prog))
    tree = parse(src)
    return infer_from_ast(tree)

def infer_from_ast(ast) -> type:
    if (_print_ast):
        print_ast(ast)

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
        unknown(prog)

def _stmt(s) -> type:
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
    elif (t == Pass):
        return None
    else:
        unknown(s)

def _expr(e) -> type:
    t = type(e)

    if (t == Constant):
        return _constant(e)
    elif (t == Name):
        return _name(e)
    elif (t == Call):
        return _call(e)
    elif (t == JoinedStr):
        return _joinedStr(e)
    else:
        unknown(e)

def _joinedStr(s: JoinedStr) -> type:
    return str

def _call(c: Call) -> type:
    return None

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
    if (a.arg == 'self'): return

    _environment[a.arg] = _toTyp(a.annotation.id)

def _assign(a : Assign) -> type:
    for target in a.targets:
        _environment[target.id] = _evalConstant(a.value)

def _evalConstant(c: Constant) -> int:
    return c.value

def _constant(c: Constant) -> type:
    return type(c.value)

def _name(n: Name) -> type:
    if n.id in _environment:
        return _environment[n.id]

def _expression(e : Expr) -> type:
    return _expr(e.value)

def _toTyp(s: str) -> type:
    if (s == 'int'):
        return int
    elif (s == 'str'):
        return str
    else:
        unknown(s)

def unknown(u):
    raise Exception("Unknown type: " + str(type(u)))
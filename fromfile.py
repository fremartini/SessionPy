import inspect, ast
from infer import print_ast

assignments = {}
exprs = {}

def check_file(f):
    file = inspect.getfile(f)
    src = _read_src_from_file(file)

    tree : ast.Module = ast.parse(src)
    print_ast(tree)
    _module(tree)
    print(assignments)
    print(exprs)
    return f

def _module(m : ast.Module):
    body = m.body
    for b in body:
        b_typ = type(b)

        if (b_typ == ast.FunctionDef):
            _function_def(b)

def _function_def(f : ast.FunctionDef):
    body = f.body
    for b in body:
        b_typ = type(b)

        if (b_typ == ast.Assign):
            _assign(b)
        elif (b_typ == ast.Expr):
            _expr(b)

def _expr(e : ast.Expr):
    value = e.value
    value_typ = type(value)

    if (value_typ == ast.Call):
        _call(value)

def _assign(a : ast.Assign):
    target = _name(a.targets[0])
    value = a.value
    value_typ = type(value)

    if (value_typ == ast.Call):
        _call(value)

    assignments[target] = value

def _call(c : ast.Call):
    func = c.func
    func_typ = type(func)
    args = c.args

    if (func_typ == ast.Subscript):
        _subscript(func)
    elif (func_typ == ast.Attribute):
        (val, attr) = _attribute(func)

        if (attr == 'send' or attr == 'recv'):
            if not val in exprs: exprs[val] = []
            exprs[val].append((attr, args))

def _attribute(a : ast.Attribute):
    value = _name(a.value)
    attr = a.attr
    return (value, attr)

def _subscript(s : ast.Subscript):
    value = _name(s.value)
    slice = s.slice
    slice_typ = type(slice)

    if (slice_typ == ast.Subscript):
        _subscript(slice)
    elif (slice_typ == ast.Tuple):
        _tuple(slice)

def _tuple(t : ast.Tuple):
    elts = t.elts
    
    for e in elts:
        e_typ = type(e)

        if (e_typ == ast.Name):
            _name(e)
        elif (e_typ == ast.Subscript):
            _subscript(e)

def _name(n : ast.Name):
    return n.id

def _read_src_from_file(file):
    with open(file, "r") as f:
        return f.read()
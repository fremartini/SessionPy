import ast

def infer(expr) -> type:
    #TODO: currently we only support constants, expand with function calls, expressions etc?
    if isinstance(expr, ast.Constant):
        arg = expr.value
    
    #print(f"argument infered to be type {type(arg)}")
    return type(arg)
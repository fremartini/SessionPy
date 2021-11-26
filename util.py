import ast

def dump(s, obj):
  print(s, "=")
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))
  print()

def dump_ast(exp):
    print(ast.dump(exp, indent=4))
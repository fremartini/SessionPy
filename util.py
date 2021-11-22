def dump(s = "\n", obj = None):
  print(s, "=")
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))
  print()
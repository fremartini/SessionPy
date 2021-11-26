def dump(s, obj):
  print(s, "=")
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))
  print()
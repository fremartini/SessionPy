from ast import dump


def debug_print(*args) -> None:
    debug = True
    if debug:
        print(*args)
        print()


def dump_ast(node) -> None:
    print(dump(node, indent=4))


def is_a(obj):
    print(obj, 'is a', type(obj))


def dump_object(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))

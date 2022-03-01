from ast import dump

DEBUG = True

def dump_ast(s, node) -> None:
    print(f'{s}\n', dump(node, indent=4))

"""
    prints object and its type
    examples:
        is_a("hello")   => 'hello is a str'
        is_a([1,2,3])   => '[1,2,3] is a list'
        is_a(str)       => 'str is a type'
"""
def is_a(obj):
    print(obj, 'is a', type(obj))


def fail_if(e: bool, msg: str) -> None:
    if e:
        raise Exception(msg)



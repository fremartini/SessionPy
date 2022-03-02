from typing import *
import typing
from types import GenericAlias, BuiltinFunctionType

from typecheck.debug import debug_print

FunctionTyp = list  # of types
ContainerType = Union[typing._GenericAlias, GenericAlias]
Typ = Union[type, FunctionTyp, ContainerType]
Environment = dict[str, Typ]


def is_type(opt_typ):
    return isinstance(opt_typ, Typ)


def read_src_from_file(file) -> str:
    with open(file, "r") as f:
        return f.read()


def can_upcast_to(t1: type, t2: type):
    if t2 == Any:
        return True
    # FIXME: issubclass is broken => issubclass(int, float) -> false. Find better solution
    return False


def can_downcast_to(t1: type, t2: type):
    if t1 == Any:
        return True

    # FIXME: issubclass is broken => issubclass(int, float) -> false. Find better solution
    return False


def union(t1: Typ, t2: Typ) -> Typ:
    """
        Unionises two types based on their hierachical structure/class relation.
        
        Examples:
            union(int, float)               => float

            union(A, B) when A is supertype => A

            union(int, str)                 => Error - unrelated hierarchies       
    """
    debug_print(f'union: called with {t1} and {t2}')
    if t1 == Any: return t2
    if t2 == Any: return t1
    if t1 == t2: return t1
    numerics: List[type] = [float, complex, int, bool, Any]  # from high to low
    sequences: List[type] = [str, tuple, bytes, list, bytearray, Any]
    if t1 in numerics and t2 in sequences or t1 in sequences and t2 in numerics:
        raise TypeError(f'cannot merge different hierarchies of {t1} and {t2}')
    for typ_hierarchy in [numerics, sequences]:
        if t1 in typ_hierarchy and t2 in typ_hierarchy:
            for typ in typ_hierarchy:
                if t1 == typ or t2 == typ:
                    return typ
    # Check if from typing module, i.e. List, Sequence, Tuple, etc.
    if isinstance(t1, ContainerType) and isinstance(t2, ContainerType):

        if t1._name != t2._name:
            raise TypeError("cannot union different typing constructs")

        if t1._name in ['Tuple', 'Dict']:
            return pack_type(Tuple if t1._name == 'Tuple' else Dict,
                             [union(t1, t2) for t1, t2 in zip(t1.__args__, t2.__args__)])
        elif t1._name == 'List':
            t1, t2 = t1.__args__[0], t2.__args__[0]
            return List[union(t1, t2)]
        else:
            raise TypeError(f"cannot union {t1._name} yet")

        # TODO: Extend with other collections 
    else:
        if issubclass(t1, t2):
            return t2
        elif issubclass(t2, t1):
            return t1
        else:
            raise TypeError(f"exhausted: could not union {t1} with {t2}")


def to_typing(typ: type):
    """
        Idea: convert lowercase types of type GenericAlias to typing types:

        Examples:
            list    => List
            dict    => Dict
    """
    if typ == list:
        return List
    elif typ == dict:
        return Dict
    elif typ == tuple:
        return Tuple
    elif typ == any:
        return Any
    else:
        raise Exception(f'to_typing: unsupported built-in type: {typ}')


def pack_type(container: Typ, types: List[Typ]):
    debug_print('pack_type', container, types)
    match len(types):
        case 1:
            return container[types[0]]
        case 2:
            return container[types[0], types[1]]
        case 3:
            return container[types[0], types[1], types[2]]
        case 4:
            return container[types[0], types[1], types[2], types[3]]
        case _:
            raise Exception(f"pack_type: supporting up to four types now; {container}[{types}] needs support")

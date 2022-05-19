from sys import builtin_module_names
from typing import *
import typing
from types import GenericAlias, ModuleType
import os
from pydoc import locate
from typing import Any, List, Tuple
from collections import namedtuple

from debug import debug_print
from sessiontype import SessionType
from ast import AST

FunctionTyp = list  # of types
ContainerType = Union[typing._GenericAlias, GenericAlias, typing._SpecialGenericAlias, tuple]
ClassTypes = str
Typ = Union[type, FunctionTyp, ContainerType, ClassTypes]

SessionStub = namedtuple('SessionStub', 'stub')


class SessionException(TypeError):
    def __init__(self, message: str, nd:AST=None) -> None:
        if nd:
            message = f"at line {nd.lineno}: {message}"
        super().__init__(message)

class StaticTypeError(TypeError):  # Show-off: not just a standard Pythonic runtime typeerror
    def __init__(self, message: str, nd:AST=None) -> None:
        if nd:
            message = f"at line {nd.lineno}: {message}"
        super().__init__(message)

class UnexpectedInternalBehaviour(Exception):
    def __init__(self, message: str, nd:AST=None) -> None:
        if nd:
            message = f"at line {nd.lineno}: {message}"
        super().__init__(message)  


class IllegalArgumentException(TypeError):
    ...


class IllegalArgumentException(TypeError):
    ...


def is_type(opt_typ):
    return isinstance(opt_typ, Typ)


def read_src_from_file(file) -> str:
    with open(file, 'r') as f:
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


def expect(e: bool, msg: str, ast_node: AST=None, exc: Type[Exception] = SessionException) -> None:
    if not e:
        raise exc(msg, ast_node)


def fail_if_cannot_cast(a: type, b: type, err: str) -> None:
    types_differ = a != b
    can_downcast: bool = can_downcast_to(a, b)  # any -> int
    can_upcast: bool = can_upcast_to(a, b)  # int -> any

    fail_if(types_differ and not (can_upcast or can_downcast), err)


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
        raise TypeError(f'unable to unify <{type_to_str(t1)}> and <{type_to_str(t2)}>')
    for typ_hierarchy in [numerics, sequences]:
        if t1 in typ_hierarchy and t2 in typ_hierarchy:
            for typ in typ_hierarchy:
                if t1 == typ or t2 == typ:
                    return typ
    # Check if from typing module, i.e. List, Sequence, Tuple, etc.
    if isinstance(t1, ContainerType) and isinstance(t2, ContainerType):

        if t1._name != t2._name:
            raise TypeError(f"cannot union different parameterised types: {t1._name} != {t2._name}")

        if t1._name in ['Tuple', 'Dict']:
            res = parameterize(Tuple if t1._name == 'Tuple' else Dict,
                               [union(t1, t2) for t1, t2 in zip(t1.__args__, t2.__args__)])
            return res
        elif t1._name == 'List':
            t1, t2 = t1.__args__[0], t2.__args__[0]
            res = List[union(t1, t2)]
            return res
        else:
            raise TypeError(f"cannot union {t1._name} yet")

        # TODO: Extend with other collections 
    else:
        if issubclass(t1, t2):
            return t2
        elif issubclass(t2, t1):
            return t1
        else:
            raise TypeError(f"exhausted: could not union {type_to_str(t1)} with {type_to_str(t2)}")


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
    elif isinstance(typ, ModuleType):
        return typ.__name__
    else:
        raise Exception(f'to_typing: unsupported built-in type: {typ}')


def parameterize(container: Typ, typ: List[Typ] | type) -> str | list[Any] | tuple[Any, ...] | Any:
    debug_print('parameterize', container, typ)
    if isinstance(typ, type):
        return container[typ]
    else:
        match len(typ):
            case 1:
                return container[typ[0]]
            case 2:
                return container[typ[0], typ[1]]
            case 3:
                return container[typ[0], typ[1], typ[2]]
            case 4:
                return container[typ[0], typ[1], typ[2], typ[3]]
            case _:
                raise Exception(f"parameterize: supporting up to four types now; {container}[{typ}] needs support")


def get_dir(path: str):
    return os.path.dirname(os.path.realpath(path))


def ch_to_mod_dir(mod_name: str):
    """
    Localises module given as string in any subdirectory recursively, and changes to this.
    Raises exception if module cannot be located.
    """
    target_dir = None
    for cur_dir, _, files in os.walk('.'):
        if mod_name in files:
            target_dir = cur_dir
            break
    if not target_dir:
        raise ModuleNotFoundError(f"imported module {mod_name} couldn't be located in any subdirectories")
    os.chdir(target_dir)


def channels_str(channels):
    res = ''
    for ch_name in channels:
        res += f'"{ch_name}": {channels[ch_name]}\n'
    return res


def str_to_typ(s: str) -> type:
    py_files_in_dir = [fname.split('.')[0].lower() for fname in os.listdir() if os.path.splitext(fname)[1] == '.py']
    if s in ['main', 'Channel'] or s in builtin_module_names or s.lower() in py_files_in_dir:
        return s
    opt = locate(s)
    opt_lower = locate(s.lower())
    if not opt and opt_lower:
        opt = to_typing(opt_lower)
    if opt == 'builtins':
        return str
    return opt


def assert_eq(expected, actual):
    if not expected == actual:
        raise Exception("expected " + str(expected) + ", found " + str(actual))


def type_to_str(typ: Typ) -> str | tuple:
    if isinstance(typ, type):
        return typ.__name__
    elif isinstance(typ, typing._GenericAlias):
        elements = [type_to_str(_) for _ in typ.__args__]
        return f'{typ.__origin__.__name__}[{",".join(elements)}]'
    elif typ == Any:
        return 'Any'
    else:
        return typ

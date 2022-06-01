from sys import builtin_module_names
from typing import *
import typing
from types import GenericAlias, ModuleType
import os
from pydoc import locate
from typing import Any, List, Tuple
from collections import namedtuple

from debug import debug_print
from ast import AST

FunctionTyp = list  # of types
ParameterisedType = Union[typing._GenericAlias, GenericAlias, typing._SpecialGenericAlias, tuple]
ClassTypes = str
Typ = Union[type, FunctionTyp, ParameterisedType, ClassTypes]

SessionStub = namedtuple('SessionStub', 'stub')


class SessionException(TypeError):
    """
    General session type exception; thrown when invalid usage of session types.
    """
    def __init__(self, message: str, current_state: AST = None) -> None:
        if current_state:
            message = f"at line {current_state.lineno}: {message}"
        super().__init__(message)


class StaticTypeError(TypeError): 
    """
    A type error found during static check of Python AST.
    """  
    def __init__(self, message: str, current_state: AST = None) -> None:
        if current_state:
            message = f"at line {current_state.lineno}: {message}"
        super().__init__(message)


class UnexpectedInternalBehaviour(Exception):
    """
    Error for internal unexpected behaviour that should be investigated.
    """
    def __init__(self, message: str, current_state: AST = None) -> None:
        if current_state:
            message = f"at line {current_state.lineno}: {message}"
        super().__init__(message)


class IllegalArgumentException(TypeError):
    """
    Error for illegal argument to a function.
    """
    ...


def is_type(opt_typ):
    """
    Checks that a given object belongs to typing family Typ.
    """
    return isinstance(opt_typ, Typ)


def read_src_from_file(file) -> str:
    """
    Returns
    -------
    str
        content of provided source file as string
    """
    with open(file, 'r') as f:
        return f.read()


def expect(e: bool, msg: str, ast_node: AST = None, exc: Type[Exception] = SessionException) -> None:
    """
    Assert-like helper to throw specified exceptions; expects some testing
    condition along with a message, and optionally AST node and specific
    exception. AST nodes help provide insight into where the error is found
    in the source program.

    Raises
    ------
    SessionException
        if none other specified
    """
    if not e:
        raise exc(msg, ast_node)


def fail_if_cannot_cast(a: type, b: type, err: str) -> None:
    """
    Tries to up/down cast, fails if cannot.
    """
    types_differ = a != b
    can_downcast: bool = a == Any  # any -> int
    can_upcast: bool = b == Any  # int -> any
    expect(not types_differ or (can_upcast or can_downcast), err)


def union(t1: Typ, t2: Typ) -> Typ:
    """
    Union two types based on their hierachical structure/class relation.
    
    Examples:
    - union(int, float)       -> float
    - union(A, B) when B <: A -> A
    - union(int, str)         -> Error: unrelated hierarchies   

    Returns
    -------
    Typ
        t2 if t1 <: t2, otherwise t1
    """
    debug_print(f'union: called with {t1} and {t2}')
    if t1 == Any:
        return t2
    if t2 == Any:
        return t1
    if t1 == t2:
        return t1
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
    if isinstance(t1, ParameterisedType) and isinstance(t2, ParameterisedType):

        if t1._name != t2._name:
            raise TypeError(f"cannot union different parameterised types: {t1._name} != {t2._name}")

        if t1._name in ['Tuple', 'Dict']:
            res = parameterise(Tuple if t1._name == 'Tuple' else Dict,
                               [union(t1, t2) for t1, t2 in zip(t1.__args__, t2.__args__)])
            return res
        elif t1._name == 'List':
            t1, t2 = t1.__args__[0], t2.__args__[0]
            res = List[union(t1, t2)]
            return res
        else:
            raise TypeError(f"cannot union {t1._name} yet")
    else:
        if issubclass(t1, t2):
            return t2
        elif issubclass(t2, t1):
            return t1
        else:
            raise TypeError(f"exhausted: could not union {type_to_str(t1)} with {type_to_str(t2)}")


def to_typing(typ: type) -> ParameterisedType:
    """
    Convert lowercase types of type GenericAlias to typing._GenericAlias.
    Examples:
    - list -> List
    - dict -> Dict
    
    Returns
    -------
    ParameterisedType
        typing._GenericAlias (ParameterisedType)
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
    return typ


def parameterise(container: Typ, typ: List[Typ] | type) -> str | list[Any] | tuple[Any, ...] | Any:
    """
    Helper function to parameterise a container type with a given list of types.
    Examples:
    - parameterise(List, [int]) => List[int]
    - parameterise(Tuple, [int, str]) => Tuple[int, str]

    Returns
    -------
    ParameterisedType
    """
    debug_print('parameterise', container, typ)
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
                raise Exception(f"parameterise: supporting up to four types now; {container}[{typ}] needs support")


def get_dir(path: str):
    """
    Returns
    -------
    str
        directory name from provided path
    """
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



def str_to_typ(s: str) -> Typ:
    """
    A (poorly written) function that will convert a string representing a known type, to the actual type.
    - str_to_typ("int") -> int (type)
    - str_to_typ("List[int]") -> List[int] (typing._GenericAlias)
    """
    py_files_in_dir = [fname.split('.')[0].lower() for fname in os.listdir() if os.path.splitext(fname)[1] == '.py']
    if s in ['main', 'Endpoint'] or s in builtin_module_names or s.lower() in py_files_in_dir:
        return s
    opt = locate(s)
    opt_lower = locate(s.lower())
    if not opt and opt_lower:
        opt = to_typing(opt_lower)
    if opt == 'builtins':
        return str
    return opt


def type_to_str(typ: Typ) -> str:
    """
    From a type, get the string representation.
    - type_to_str(int) -> "int"
    - type_to_str(Dict[str, bool]) -> "Dict[str, bool]"
    """
    if isinstance(typ, type):
        return typ.__name__
    elif isinstance(typ, typing._GenericAlias):
        elements = [type_to_str(_) for _ in typ.__args__]
        return f'{typ.__origin__.__name__}[{",".join(elements)}]'
    elif typ == Any:
        return 'Any'
    else:
        return typ

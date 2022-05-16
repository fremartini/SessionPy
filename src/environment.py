from __future__ import annotations

from enum import Enum

from lib import *
from debug import debug_print
from typing import Union


class Category(Enum):
    VARIABLE = 0
    FUNCTION = 1
    NESTED = 2


def empty() -> dict:
    return {env_typ: {} for env_typ in list(Category)}


class Environment:
    def __init__(self, env: dict = None):
        if env is None:
            env = empty()
        self.environment = env

    def lookup_var(self, v: str) -> Typ:
        if v in self.environment[Category.VARIABLE]:
            return self.environment[Category.VARIABLE][v]
        else:
            raise EnvironmentError(f'{v} not found in {self.environment[Category.VARIABLE]}')

    def lookup_func(self, key: str) -> Typ:
        if key in self.environment[Category.FUNCTION]:
            return self.environment[Category.FUNCTION][key]
        else:
            raise EnvironmentError(f'{key} not found in {self.environment[Category.FUNCTION]}')

    def lookup_nested(self, f: str) -> Environment:
        return self.environment[Category.NESTED][f]

    def lookup_or_default(self, k: str, default: Any) -> Union[Typ, dict[str, Typ], str]:
        try:
            return self.lookup(k)
        except EnvironmentError:
            return default

    def lookup_var_or_default(self, k: str, default: Any) -> Union[Typ, dict[str, Typ], str]:
        try:
            return self.lookup_var(k)
        except EnvironmentError:
            return default

    def lookup_func_or_default(self, k: str, default: Any) -> Union[Typ, dict[str, Typ], str]:
        try:
            return self.lookup_func(k)
        except EnvironmentError:
            return default

    def contains_nested(self, k: str) -> bool:
        return k in self.environment[Category.NESTED]

    def contains_function(self, f: str) -> bool:
        return f in self.environment[Category.FUNCTION]

    def contains_variable(self, v: str) -> bool:
        return v in self.environment[Category.VARIABLE]

    def bind_var(self, var: str, typ: Typ) -> None:
        self.environment[Category.VARIABLE][var] = typ

    def bind_func(self, f: str, typ: Typ) -> None:
        self.environment[Category.FUNCTION][f] = typ

    def bind_nested(self, key: str, env: Environment) -> None:
        self.environment[Category.NESTED][key] = env

    def lookup(self, key: str) -> Typ:
        debug_print(f'lookup: searching for key="{key}" in {self.environment}')
        priority = [Category.VARIABLE, Category.FUNCTION, Category.NESTED]
        for env_cat in priority:
            if key in self.environment[env_cat]:
                return self.environment[env_cat][key]
        raise EnvironmentError(f"'{key}' was not found in {self.environment}")

    def get_vars(self):
        variables: dict = self.environment[Category.VARIABLE]
        return variables.items()

    def try_find(self, key):
        try:
            return self.lookup(key)
        except EnvironmentError:
            return None

    def get_kind(self, kind: type) -> list[tuple[str, type]]:
        items = []
        for (key, val) in self.get_vars():
            if isinstance(val, kind):
                items.append((key, val))
        return items

    def __str__(self) -> str:
        res = "{"
        for key in self.environment:
            res += f'\n  {key}=\n'
            inner_env = self.environment[key]
            for key1 in inner_env:
                res += f'    {key1} = {inner_env[key1]}\n'
        return res + "}"

    def __repr__(self):
        return self.__str__()

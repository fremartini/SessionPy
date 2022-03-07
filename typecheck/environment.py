from __future__ import annotations
from enum import Enum
from lib import *
from debug import debug_print
from typing import Union, List
from types import FunctionType


class Category(Enum):
    CLASS = 0
    VARIABLE = 1
    FUNCTION = 2
    IMPORT = 3


class Environment(dict):  
    def __init__(self):
        self.environment = { env_typ: {} for env_typ in list(Category) }
        
    def lookup_class(self, c : str) -> dict[str, Typ]:
        return self.environment[Category.CLASS][c]

    def lookup_var(self, v : str) -> Typ:
        return self.environment[Category.VARIABLE][v]

    def lookup_func(self, f : str) -> Typ:
        return self.environment[Category.FUNCTION][f]

    def lookup_import(self, f : str) -> dict[str, Typ]:
        return self.environment[Category.FUNCTION][f]

    def lookup_or_default(self, k : str) -> Union[Typ, dict[str, Typ], str]:
        try:
            return self.lookup(k)
        except:
            return k
    
    def bind_class(self, cl: str, typ: Dict[str, Typ]) -> None:
        key = f"class_{cl}"
        env = self.environment[Category.CLASS] 

        if key in env:
            env[key] = env[key] | typ
        else:
            env[key] = typ

    def bind_var(self, var: str, typ: Typ) -> None:
        self.environment[Category.VARIABLE][var] = typ

    def bind_func(self, f : str, typ: Typ):
        self.environment[Category.FUNCTION][f] = typ

    def bind_import(self, module_name : str, env: Environment):
        self.environment[Category.IMPORT][module_name] = env

    def lookup(self, key : str) -> Typ:
        debug_print(f'lookup: searching for key="{key}" in {self.environment}')
        priority = [Category.VARIABLE, Category.FUNCTION, Category.CLASS, Category.IMPORT]
        for env_cat in priority:
            if key in self.environment[env_cat]:
                return self.environment[env_cat][key]
        raise EnvironmentError(f"'{key}' was not found in {self.environment}")

    def __str__(self) -> str:
        return str(self.environment)
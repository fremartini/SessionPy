from typing import *


# TODO(Johan): Let this be for now in case `type` construct will
class Typ:
    def __str__(self) -> str:
        return


class TypInt(Typ):
    def __repr__(self) -> str:
        return "int"

    def __str__(self) -> str:
        return self.__repr__()


class TypFunc(Typ):
    def __init__(self, parameters: List[Typ], returns: Typ) -> None:
        self.parameters = parameters
        self.returns = Any if returns == None else returns

    def __repr__(self) -> str:
        return f"{' -> '.join([str(_) for _ in self.parameters])} -> {self.returns}"

    def __str__(self) -> str:
        return self.__repr__()


class TypStr(Typ):
    def __repr__(self) -> str:
        return "string"

    def __str__(self) -> str:
        return self.__repr__()


class TypFloat(Typ):
    def __repr__(self) -> str:
        return "float"

    def __str__(self) -> str:
        return self.__repr__()


class TypBool(Typ):
    def __repr__(self) -> str:
        return "bool"

    def __str__(self) -> str:
        return self.__repr__()


class TypAny():
    def __repr__(self) -> str:
        return "any"

    def __str__(self) -> str:
        return self.__repr__()


class TypObject(Typ):
    # TODO: Should receive something
    ...


### Hierarchies

class Numbers(object):
    ...


class Sequences(object):
    ...


class SetTypes(object):
    ...


class Mappings(object):
    ...

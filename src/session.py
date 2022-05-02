from types import GenericAlias
from unicodedata import name
import sessiontype
from sessiontype import Choose, Send, Recv, End, Offer, Choose, Label
from typing import ForwardRef

class Session():
    def __init__(self, typ=GenericAlias) -> None:
        self.typ = typ

    def _dual_helper(self, typ: GenericAlias):
        if typ == End:
            return End
        if isinstance(typ, ForwardRef):
            return typ.__forward_arg__
        base = typ.__origin__
        if sessiontype.has_dual(base):
            duality = sessiontype.get_dual(typ)
            if base in [Send, Recv]:
                data_typ = typ.__args__[0] 
                return duality[data_typ, self._dual_helper(typ.__args__[1])]
            elif base in [Offer, Choose]:
                return duality[self._dual_helper(typ.__args__[0]), self._dual_helper(typ.__args__[1])]

        else:
            match typ():
                case Label():
                    name = typ.__args__[0].__forward_arg__
                    duality = self._dual_helper(typ.__args__[1])
                    return Label[name, duality]

    def dual(self):
        return self._dual_helper(self.typ)

if __name__ == '__main__':
    test = Session(Send[int, Recv[str, End]])
    print(test.typ)
    print(test.dual())
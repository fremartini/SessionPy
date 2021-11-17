from enum import Enum

class Op(Enum):
    SEND = 1
    RECV = 2
    END = 3

class SessionType:
    def __init__(self, op : Op, typ : type, rest) -> None:
        self.t = (op, typ, rest)



    #Channel(SessionType(Op.SEND, int, SessionType(Op.RECV, int, SessionType(Op.END, None, None))))
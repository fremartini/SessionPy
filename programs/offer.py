from channel import Channel, Branch
from sessiontype import *

ch = Channel[Send[int, Offer[  Send[str, Recv[str, End]],  Send[int, End]  ]]]()
ch.send(5)

match ch.offer():
    case Branch.LEFT:
        ch.send("hello!")
        msg = ch.recv()

    case Branch.RIGHT:
        ch.send(42)



""""
Module(body=[Expr(value=Subscript(value=Name(id='Channel', ctx=Load()),
    slice=Tuple(elts=[Constant(value='main'), Subscript(value=Name(id='Send',
        ctx=Load()), slice=Tuple(elts=[Name(id='int', ctx=Load()),
            Constant(value='main')], ctx=Load()), ctx=Load())], ctx=Load()),
        ctx=Load()))], type_ignores=[])"
"""
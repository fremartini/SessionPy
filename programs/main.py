from channel import Channel, Branch
from sessiontype import *

ch = Channel[Label["main", Recv[str, "main"]]]()



""""
Module(body=[Expr(value=Subscript(value=Name(id='Channel', ctx=Load()),
    slice=Tuple(elts=[Constant(value='main'), Subscript(value=Name(id='Send',
        ctx=Load()), slice=Tuple(elts=[Name(id='int', ctx=Load()),
            Constant(value='main')], ctx=Load()), ctx=Load())], ctx=Load()),
        ctx=Load()))], type_ignores=[])"
"""
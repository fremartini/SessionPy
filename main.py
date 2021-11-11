from channel import Channel, send, recv

"""
Goal: make the decorator "check_channel" look for channel in parameters and
make sure it is used correctly in body
"""

def check_input_types(kwargs):

    def check_inner(f):

        for var_name, var_type in kwargs.items():

            assert (f.__annotations__[var_name] == var_type)

        return f

    return check_inner

"""

    ...: def take_type(t):
    ...:     def printType(x):
    ...:         print(t)
    ...:     return printType

In [16]: @take_type(str)
    ...: def id(x: int): return x
<class 'str'>
"""
 

@check_input_types({'chI': int, 'chS': str})
def will_send_ints(chI: Channel, chQ: Channel, chS: Channel):
    send(chI, "I lied")


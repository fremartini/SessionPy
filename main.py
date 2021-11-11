from channel import Channel
from typeChecking import check_channels

"""
Goal: make the decorator "check_channel" look for channel in parameters and
make sure it is used correctly in body
"""
 
@check_channels({'chI': int, 'chS': str})
def will_send_ints(chI: Channel, chQ: Channel, chS: Channel):
    chI.send(1)
    chS.send("1")
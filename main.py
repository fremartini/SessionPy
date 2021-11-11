from TCPchannel import Channel
from typeChecking import check_channels

"""
Goal: make the decorator "check_channel" look for channel in parameters and
make sure it is used correctly in body
"""

@check_channels({'chI': int})
def will_send_ints(chI: Channel):
    chI.send(1)

ch : Channel = Channel(int, 5001)
ch.send(141)
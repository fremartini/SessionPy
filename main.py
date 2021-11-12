from TCPchannel import Channel
from typeChecking import check_channels, check_file

@check_file
def main():
    pass
    #ch : Channel[out(int), into(bool)] = Channel(5000)
    #will_send_ints(ch)

@check_channels({'chI': int})
def will_send_ints(chI: Channel):
    chI.send(1)

if __name__ == '__main__':
    main()

#TODO: generics & simple communication
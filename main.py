from channel import Channel, send, recv

ch : Channel = Channel(int)
send(ch, 1)
send(ch, 1)
send(ch, 1)
send(ch, 1)

v = recv(ch)
print(v)
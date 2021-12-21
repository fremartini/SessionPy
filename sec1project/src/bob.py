
from os import read
from tools import *
from rsa import *
import sys


def read():
    return sign(receive(soc), alice_e, alice_n)


HOST = '127.0.0.1'
PORT = 50789

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_key = KeyPair(97, 73)
my_key.generate()

# Bob's random string
rB = rand_str(31)
try:
    # With the help of bind() function
    # binding host and port
    soc.connect((HOST, PORT))
    print('> Connected to Alice!')
    send_context(soc, my_key.pub, 'public key', 'Alice')
    alicePub = read_pub(receive(soc))
    alice_n, alice_e = alicePub

    print(f'> Received Alice\'s public key: {alicePub}')

    alice_commit = read()
    print(f'Received commit from Alice, sending it back signed as ACK')

    # Send alice_commit back as ACK
    send_signed(soc, alice_commit, 'ACK', 'Alice', my_key)

    roll_rand = read()
    assert h(roll_rand) == alice_commit
    roll = int(roll_rand[0])
    print(f'The roll was {roll}')

    # In reverse
    roll_rand = str(roll) + rB
    my_commit = h(roll_rand)
    send_signed(soc, my_commit, 'hashed commit', 'Alice', my_key)

    reply = read()
    if reply:
        # Assert Alice received the commit
        assert reply == my_commit
        send_signed(soc, roll_rand, 'roll and random string', 'Alice', my_key)


except socket.error as message:

    # if any error occurs then with the
    # help of sys.exit() exit from the program
    print('Bind failed. Error Code : '
          + str(message[0]) + ' Message '
          + message[1])
    sys.exit()

soc.close()
print('Protocol exited successfully!')

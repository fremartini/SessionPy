import socket
import sys
from tools import *
from rsa import *


def read():
    return sign(receive(conn), bob_e, bob_n)


HOST = '127.0.0.1'
PORT = 50789

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Alice's random string
rA = rand_str(31)

my_key = KeyPair(61, 53)
my_key.generate()

print("waiting for Bob to connect ...")

try:
    soc.bind((HOST, PORT))
except socket.error as message:
    print('Bind failed. Error Code : '
          + str(message[0]) + ' Message '
          + message[1])
    sys.exit(1)

# We have a connection

soc.listen(2)
conn, address = soc.accept()

# print the address of connection
print(f'# Connected with Bob on {address}!')

# Initially, sharing their public keys
bobPub = read_pub(receive(conn))
bob_n, bob_e = bobPub

send_context(conn, my_key.pub, 'my public key', 'Bob')

# Start the game
my_roll = dice_roll()
my_commit = h(my_roll, rA)
print(f'> I, Alice, rolled a {my_roll}')
send_signed(conn, my_commit, 'hashed commit', 'Bob', my_key)
reply = read()
if reply:
    # Check if Bob received the commit
    assert reply == my_commit
    send_signed(conn, str(my_roll) + rA,
                'roll and random string', 'Bob', my_key)

# Receive Bob's roll
bob_commit = read()
send_signed(conn, bob_commit, 'signed commit as ACK', 'Bob', my_key)
roll_and_rand = read()
assert h(roll_and_rand) == bob_commit
roll_return = int(roll_and_rand[0])
assert my_roll == roll_return
conn.close()
soc.close()
print('Protocol exited successfully!')

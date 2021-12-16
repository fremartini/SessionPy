import socket, sys
from tools import recv_int, send_int

HOST = '127.0.0.1'
PORT = 50789

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("waiting for Bob to connect ...")

try: soc.bind((HOST, PORT))
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
i = recv_int(conn)
print(f'received integer: {i}')

send_int(conn, 42)

conn.close()
soc.close()
print('Protocol exited successfully!')
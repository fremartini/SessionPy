import socket, sys
from util import recv_int, send_int
import sys

HOST = '127.0.0.1'
PORT = 50789

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    soc.connect((HOST, PORT))
    print('> Connected to Alice!')

    send_int(soc, 666)
    i = recv_int(soc)
    print(f'received {i} from Alice')
    
except socket.error as message:
    print('Bind failed. Error Code : '
        + str(message[0]) + ' Message '
        + message[1])
    sys.exit()

soc.close()
print('Protocol exited successfully!')

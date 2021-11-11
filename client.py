import socket               # Import socket module

s = socket.socket()         # Create a socket object
port = 5000                 # Reserve a port for your service.

s.connect(('localhost', port))
print (s.recv(1024))
s.close()                     # Close the socket when done
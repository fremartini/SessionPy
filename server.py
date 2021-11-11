import socket               # Import socket module

def strToBytes(s): return bytes(s, 'utf-8')

s = socket.socket()         # Create a socket object
port = 5000                 # Reserve a port for your service.
s.bind(('localhost', port)) # Bind to the port

s.listen(5)                 # Now wait for client connection.
while True:
   c, addr = s.accept()     # Establish connection with client.
   print ('Got connection from', addr)
   c.send(strToBytes('Thank you for connecting'))
   c.close()                # Close the connection
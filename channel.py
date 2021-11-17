from typeChecking import *
import socket
import traceback
import time

class Channel:
    host = 'localhost'

    def __init__(self, ST):
        self.ST = ST
        self.port = 5000
        self.addr = (Channel.host, self.port)

    def send(self, e):
        time.sleep(1)
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(self.addr)
            s.listen()
            print (f"Waiting for someone to recieve {str(e)}")

            c, addr = s.accept()
            c.send(bytes(str(e), 'utf-8'))
            c.close()
            
        except OSError as ex:
            s.connect(self.addr)
            s.send(bytes(str(e), 'utf-8'))
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
        finally:
            s.close()

    def recv(self):
        time.sleep(1)
        s : socket = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.connect(self.addr)
            r = s.recv(512)
            print (r)
        except OSError as ex:
            s.bind(self.addr)
            s.listen()
            print (f"Waiting for someone to send a message")

            c, addr = s.accept()
            r = c.recv(512)
            print (r)
            c.close()
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
        finally:
            s.close()
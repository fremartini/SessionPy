import time
import threading
from context import *

ch = Channel(Send[int, End])
ch1 = Channel(Recv[int, Recv])
ch.join(ch1)

ch.send("hello!")

def threading_func():
    print('trying to receive')
    a = ch.recv()
    print('got ', a)


x = threading.Thread(target=threading_func)
x.start()

#time.sleep(1)

x.join()

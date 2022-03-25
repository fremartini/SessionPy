import time
import threading
from context import *

ch = Channel[Offer[Send[str, Recv[int, End]], Send[int, End]]]()


def threading_func():
    print('trying to receive')
    a = ch.recv()
    print('got ', a)


x = threading.Thread(target=threading_func)
x.start()

time.sleep(1)
ch.send("hello!")

x.join()

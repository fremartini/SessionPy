import random
import time

from context import *

roles = {'Distributor': ('localhost', 5000), 'self': ('localhost', 5001), 'c2': ('localhost', 5002), 'c3': ('localhost', 5003),}

ch = Channel(Recv[List, 'Distributor', Send[int, 'Distributor', End]], roles)

workload = ch.recv()

time.sleep(random.randint(3, 9))

ch.send(random.randint(50, 100))

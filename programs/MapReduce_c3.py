import random
import time

from context import *

routing_table = {'Distributor': ('localhost', 5000), 'c1': ('localhost', 5001), 'c2': ('localhost', 5002), 'self': ('localhost', 5003),}

ch = Channel(Recv[List[int], 'Distributor', Send[int, 'Distributor', End]], routing_table)

workload = ch.recv()

print(workload)

time.sleep(random.randint(3, 9))

print('sending')

ch.send(random.randint(50, 100))

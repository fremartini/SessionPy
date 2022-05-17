from context import *

routing_table = {'Source': ('localhost', 0), 'self': ('localhost', 0),}

ch = Channel(Label["LOOP", Offer['Source', {"work": Recv[int, 'Source', "LOOP"], "stop": End}]], routing_table)

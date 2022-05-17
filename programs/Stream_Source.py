from context import *

routing_table = {'self': ('localhost', 0), 'Sink': ('localhost', 0),}

ch = Channel(Label["LOOP", Choose['Sink', {"work": Send[int, 'Sink', "LOOP"], "stop": End}]], routing_table)

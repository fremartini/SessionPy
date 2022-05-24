from context import *

routing_table = {'self': ('localhost', 5000), 'Sink': ('localhost', 5001)}

ch = Endpoint(Label["LOOP", Choose['Sink', {"work": Send[int, 'Sink', "LOOP"], "stop": End}]], routing_table)

i = 0

while True:
    if i < 200:
        ch.choose('work')
        ch.send(i)
    else:
        break
    i = i + 1

ch.choose('stop')

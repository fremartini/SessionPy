from context import *

routing_table = {'self': ('localhost', 5000), 'Sink': ('localhost', 5001)}

ep = Endpoint(Label["LOOP", Choose['Sink', {"work": Send[int, 'Sink', "LOOP"], "stop": End}]], routing_table)

i = 0

while True:
    if i < 200:
        ep.choose('work')
        ep.send(i)
    else:
        break
    i += 1

ep.choose('stop')

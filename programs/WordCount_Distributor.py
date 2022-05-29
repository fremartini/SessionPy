from context import *

routing_table = {'self': ('localhost', 5000), 'c1': ('localhost', 5001), 'c2': ('localhost', 5002),
                 'c3': ('localhost', 5003)}

ep = Endpoint(Send[list[str], 'c1', Send[list[str], 'c2', Send[
    list[str], 'c3', Recv[dict[str, int], 'c1', Recv[dict[str, int], 'c2', Recv[dict[str, int], 'c3', End]]]]]],
              routing_table, static_check=False)


def split(a, n):
    k, m = divmod(len(a), n)
    return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))


lists = []
with open('programs/hamlet.txt') as f:
    data = ImmutableList(
        f.read().replace('\n', ' ').replace('.', ' ').replace(':', '').replace(';', ' ').replace(',', ' ').replace('\'',
                                                                                                                   '').replace(
            ']', ' ').replace('[', ' ').replace('!', ' ').replace('-', ' ').replace('?', ' ').replace('(', '').replace(
            ')', '').split(' ')).filter(
        lambda x: x != '').map(
        lambda x: x.lower())
    lists = split(data.items(), 3)

ep.send(lists[0])
ep.send(lists[1])
ep.send(lists[2])

r1: dict[str, int] = ep.recv()
r2: dict[str, int] = ep.recv()
r3: dict[str, int] = ep.recv()

for k, v in r2.items():
    r1[k] = r1.get(k, 0) + v

for k, v in r3.items():
    r1[k] = r1.get(k, 0) + v

with open('out.txt', "w") as f:
    for k, v in r1.items():
        f.write(f'{k}: {v}\n')

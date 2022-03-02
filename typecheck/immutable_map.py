from typing import List


class ImmutableMap:
    def __init__(self, map=None):
        if map is None:
            map = {}
        self.internal_map = map

    def len(self):
        return len(self.internal_map)

    def add(self, k, v):
        c = self.internal_map.copy()
        c[k] = v
        return ImmutableMap(c)

    def contains(self, k):
        return k in self.internal_map

    def lookup(self, k):
        if not self.contains(k):
            raise Exception(f'{k} was not found in {self.internal_map}')

        return self.internal_map[k]

    def lookup_or_default(self, k, default):
        if not self.contains(k):
            return default

        return self.lookup(k)

    def items(self) -> List:
        return self.internal_map

    def __len__(self):
        return self.len()

    def __eq__(self, other):
        return self.internal_map == other.internal_map

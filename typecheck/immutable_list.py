from typing import List


class ImmutableList:
    def __init__(self, lst=None):
        if lst is None:
            lst = []
        self.internal_list = lst

    def len(self):
        return len(self.internal_list)

    def add(self, e):
        c = self.internal_list.copy()
        c.append(e)
        return ImmutableList(c)

    def head(self):
        if len(self.internal_list) == 0:
            raise Exception('Cannot take head of empty list')
        return self.internal_list[0]

    def tail(self):
        if len(self.internal_list) == 0:
            raise Exception('Cannot take tail of empty list')

        c = self.internal_list.copy()
        c.pop(0)
        return ImmutableList(c)

    def last(self):
        return self.internal_list[len(self.internal_list) - 1]

    def __len__(self):
        return self.len()

    def __eq__(self, other):
        for v, v1 in zip(self.internal_list, other.internal_list):
            if v != v1:
                return False
        return True

    def __str__(self):
        return f"{self.internal_list}"

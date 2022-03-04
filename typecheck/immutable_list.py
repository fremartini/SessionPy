class ImmutableList:
    def __init__(self, lst=None):
        if lst is None:
            lst = []
        self._internal_list = lst

    def len(self):
        return len(self._internal_list)

    def add(self, e):
        c = self._internal_list.copy()
        c.append(e)
        return ImmutableList(c)

    def head(self):
        if len(self._internal_list) == 0:
            raise Exception('Cannot take head of empty list')
        return self._internal_list[0]

    def tail(self):
        if len(self._internal_list) == 0:
            raise Exception('Cannot take tail of empty list')

        c = self._internal_list.copy()
        c.pop(0)
        return ImmutableList(c)

    def last(self):
        return self._internal_list[len(self._internal_list) - 1]

    def items(self):
        return self._internal_list

    def discard_last(self):
        c = self._internal_list.copy()
        c.pop()
        return ImmutableList(lst=c)

    def __len__(self):
        return self.len()

    def __eq__(self, other):
        for v, v1 in zip(self._internal_list, other.items()):
            if v != v1:
                return False
        return True

    def __str__(self):
        return f"{self._internal_list}"

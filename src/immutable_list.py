from typing import List, Generic, TypeVar

T = TypeVar('T')


class ImmutableList(Generic[T]):
    def __init__(self, _list=None):
        if _list is None:
            _list = []
        self._internal_list = _list

    @staticmethod
    def of_list(elements: List[T]):
        return ImmutableList(_list=elements)

    def len(self) -> int:
        return len(self._internal_list)

    def add(self, e):
        c = self._internal_list.copy()
        c.append(e)
        return ImmutableList.of_list(c)

    def head(self) -> T:
        if len(self._internal_list) == 0:
            raise Exception('Cannot take head of empty list')
        return self._internal_list[0]

    def tail(self):
        if len(self._internal_list) == 0:
            raise Exception('Cannot take tail of empty list')

        c = self._internal_list.copy()
        c.pop(0)
        return ImmutableList(c)

    def last(self) -> T:
        return self._internal_list[len(self._internal_list) - 1]

    def items(self) -> List[T]:
        return self._internal_list

    def discard_last(self):
        c = self._internal_list.copy()
        c.pop()
        return ImmutableList.of_list(c)

    def map(self, f):
        lst = ImmutableList()
        for elem in self._internal_list:
            lst = lst.add(f(elem))
        return lst

    def __len__(self):
        return self.len()

    def __eq__(self, other):
        for v, v1 in zip(self._internal_list, other.items()):
            if v != v1:
                return False
        return True

    def __str__(self):
        return f"{self._internal_list}"

    def __repr__(self) -> str:
        return f"ImmutableList{self.__str__()}"

    def __iter__(self):
        return iter(self._internal_list)

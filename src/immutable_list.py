from __future__ import annotations

from functools import reduce
from typing import List, Generic, TypeVar, Callable, Iterator, Any

T = TypeVar('T')
K = TypeVar('K')


class ImmutableList(Generic[T]):
    def __init__(self, _list=None):
        if _list is None:
            _list = []
        self._internal_list: List[T] = _list

    def len(self) -> int:
        return len(self._internal_list)

    def add(self, e) -> ImmutableList[T]:
        c = self._internal_list.copy()
        c.append(e)
        return ImmutableList(c)

    def head(self) -> T:
        if len(self._internal_list) == 0:
            raise Exception('Cannot take head of empty list')
        return self._internal_list[0]

    def tail(self) -> ImmutableList[T]:
        if len(self._internal_list) == 0:
            raise Exception('Cannot take tail of empty list')

        c = self._internal_list.copy()
        c.pop(0)
        return ImmutableList(c)

    def last(self) -> T:
        return self._internal_list[len(self._internal_list) - 1]

    def items(self) -> List[T]:
        return self._internal_list

    def discard_last(self) -> ImmutableList[T]:
        c = self._internal_list.copy()
        c.pop()
        return ImmutableList(c)

    def map(self, f: Callable[[T], K]) -> ImmutableList[K]:
        return self.fold(lambda acc, x: acc.add(f(x)), ImmutableList())

    def fold(self, f: Callable[[List[K], T], List[K]], initial: K) -> K:
        return reduce(lambda acc, x: f(acc, x), self._internal_list, initial)

    def filter(self, f: Callable[[T], bool]) -> ImmutableList[T]:
        return self.fold(lambda acc, x: acc.add(x) if f(x) else acc, ImmutableList())

    def __len__(self):
        return self.len()

    def __eq__(self, other: Any):

        if not type(self) == type(other):
            return False

        if not len(self) == len(other):
            return False

        for v, v1 in zip(self._internal_list, other.items()):
            if v != v1:
                return False
        return True

    def __str__(self) -> str:
        return f'ImmutableList{self._internal_list}'

    def __repr__(self) -> str:
        return self.__str__()

    def __iter__(self) -> Iterator[T]:
        return iter(self._internal_list)

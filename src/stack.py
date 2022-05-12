from typing import Any, TypeVar, Generic

from immutable_list import ImmutableList

T = TypeVar('T')


class Stack(Generic[T]):
    def __init__(self):
        self.stack = ImmutableList()

    def push(self, e: Any) -> None:
        self.stack = self.stack.add(e)

    def pop(self) -> T:
        if len(self.stack) == 0:
            raise Exception('empty stack')

        last = self.stack.last()

        self.stack = self.stack.discard_last()

        return last

    def peek(self) -> T:
        return self.stack.last()

    def isEmpty(self) -> bool:
        return len(self.stack) == 0

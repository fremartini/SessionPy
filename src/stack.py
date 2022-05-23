from typing import Any, TypeVar, Generic

from immutable_list import ImmutableList

T = TypeVar('T')


class Stack(Generic[T]):
    """Stack data structure

    Attributes
    ----------
    _lst: ImmutableList
        internal list of the datastructure
    """

    def __init__(self):
        self._lst: ImmutableList = ImmutableList()

    def push(self, e: Any) -> None:
        """Push an element onto the stack

        Parameters
        ----------
        e: Any
            element to be pushed onto the stack
        """
        self._lst = self._lst.add(e)

    def pop(self) -> T:
        """Pops the top element of the stack.
        Throws an exception if the stack is empty

        Returns
        -------
        T
            the top element on the stack
        """
        if len(self._lst) == 0:
            raise Exception('empty stack')

        top = self._lst.last()

        self._lst = self._lst.discard_last()

        return top

    def peek(self) -> T:
        """Look at the top element of the stack without popping it

        Returns
        -------
        T
            the top element of the stack
        """

        return self._lst.last()

    def is_empty(self) -> bool:
        """Check if the stack is empty

        Returns
        -------
        bool
            if the stack is empty
        """
        return len(self._lst) == 0

    def __repr__(self) -> str:
        return str(self._lst)

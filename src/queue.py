from typing import Any, TypeVar, Generic

from immutable_list import ImmutableList

T = TypeVar('T')


class Queue(Generic[T]):
    """Queue data structure

    Attributes
    ----------
    _lst: ImmutableList
        internal list of the datastructure
    """

    def __init__(self):
        self._lst: ImmutableList = ImmutableList()

    def enqueue(self, e: Any) -> None:
        """Enqueues an element

        Parameters
        ----------
        e: Any
            element to be enqueued
        """
        self._lst = self._lst.add(e)

    def dequeue(self) -> T:
        """Dequeue the oldest element.
        Throws an exception if the queue is empty

        Returns
        -------
        T
            the oldest element in the queue
        """
        if len(self._lst) == 0:
            raise Exception('empty queue')

        fst = self._lst.head()

        self._lst = self._lst.tail()

        return fst

    def peek(self) -> T:
        """Look at the first element of the queue

        Returns
        -------
        T
            the next element to dequeue
        """

        return self._lst.head()

    def isEmpty(self) -> bool:
        """Check if the queue is empty

        Returns
        -------
        bool
            if the queue is empty
        """
        return len(self._lst) == 0

    def __repr__(self) -> str:
        return str(self._lst)

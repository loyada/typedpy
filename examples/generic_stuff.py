from typing import TypeVar, Generic

T = TypeVar("T")


class Stack(Generic[T]):
    def __init__(self, i: int, t: T) -> None:
        # Create an empty list with items of type T
        self.items: list[T] = []
        self.i = i
        self._t = t

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()

    def empty(self) -> bool:
        return not self.items


def func(stack: Stack[int]):
    pass

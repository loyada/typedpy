import enum
import typing
from typing import Callable, Iterable, Iterator, Mapping, Optional, TypeVar

from .enums import State
from .more_classes import Person
from typedpy import (
    AnyOf,
    Anything,
    DateTime, Enum,
    Extend, Float,
    ImmutableStructure,
    Integer,
    Map,
    Omit,
    Partial,
    Pick,
    Set,
    Structure,
    mappers,
)
from typedpy import create_pyi


# Note that Person will require importing Address in the pyi file
class Employee(Extend[Person]):
    ssid: str


def func(x=5, *, e: Employee = None, **kw) -> Mapping[str, str]:
    print(f"{x}, {e}")
    return State.FL


T = TypeVar("T")

def func2(t: T) -> list[T]:
    pass


class Blah(Structure):
    i = Integer
    d: Map[str, int] = dict
    s: str
    person: Person
    dob: DateTime
    arr: list[str]
    _serialization_mapper = mappers.TO_LOWERCASE


class Foo(Blah, ImmutableStructure):
    a: set
    b: Set()
    union = AnyOf[int, str]
    any = Anything

    _serialization_mapper = mappers.TO_LOWERCASE

    def get_double_aa(self, x: Optional[int], p: Person = None) -> str:
        return f'{self.a}{x}'

    def doit(self):
        pass

    @staticmethod
    def aaa() -> str:
        return "aaaaa"


class FooPartial(Partial[Foo]):
    x: str


class FooOmit(Omit[Foo, ("a", "b")]):
    x: int


class FooPick(Pick[Foo, {"d", "a"}]):
    xyz: float


class Bar(Foo.omit("a", "b")):
    x: int
    opt: Optional[Float]
    state: Enum[State]


class State1(enum.Enum):
    NY = 1
    NJ = 2
    AL = 3
    FL = 4


def bbb() -> Callable[[Bar, str], Iterable[Foo]]:
    return None  # noqa


def ccc() -> Callable[[T], None]:
    pass


def ddd() -> [int, str, ...]:
    return [1,"xx"]


def eee(x: Optional[int] = 4, arr: list[str] = list) -> Optional[int]:
    return 3


def fff(c: Optional[Callable]) -> Iterator[str]:
    pass

def ggg() -> typing.Tuple:
    return (1,2,3)


if __name__ == "__main__":
    create_pyi(__file__, locals())

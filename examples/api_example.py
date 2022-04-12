from typing import Optional

from examples.enums import State
from examples.more_classes import Person
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


class Blah(Structure):
    i = Integer
    d: Map[str, int] = dict
    s: str
    person: Person
    dob: DateTime

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


if __name__ == "__main__":
    create_pyi(__file__, locals())

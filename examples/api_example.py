import enum
from typing import Optional

from typedpy import (
    AnyOf,
    Anything,
    Enum,
    Float,
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


class State(enum.Enum):
    NY = 1
    NJ = 2
    AL = 3
    FL = 4


class Blah(Structure):
    i = Integer
    d: Map[str, int] = dict
    s: str

    _serialization_mapper = mappers.TO_LOWERCASE


class Foo(Blah, ImmutableStructure):
    a: set
    b: Set()
    union = AnyOf[int, str]
    any = Anything

    _serialization_mapper = mappers.TO_LOWERCASE


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

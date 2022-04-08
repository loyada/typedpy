from typedpy import ImmutableStructure, Integer, Map, Omit, Partial, Pick, Set, Structure, TypedField, mappers
from typedpy import create_pyi


class Blah(Structure):
    i = Integer
    d: Map[str, int] = dict
    s: str

    _serialization_mapper = mappers.TO_LOWERCASE


class Foo(Blah, ImmutableStructure):
    a: set
    b: Set()

    _serialization_mapper = mappers.TO_LOWERCASE


class FooPartial(Partial[Foo]):
        x: str


class FooOmit(Omit[Foo, ("a", "b")]):
    x: int


class FooPick(Pick[Foo, {"d","a"}]):
    xyz: float


if __name__=="__main__":
    create_pyi(__file__, locals())
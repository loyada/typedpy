from typedpy import Array, FunctionCall, ImmutableStructure, Integer, Map, Omit, Structure, mappers


def build_default_dict():
    return {"abc": 0}


class Blah(Structure):
    i: int
    d: Map[str, int] = build_default_dict
    a: str


class Foo(Blah, ImmutableStructure):
    s: set
    b: Integer

    _serialization_mapper = mappers.TO_LOWERCASE


Example9 = Omit[Foo, ("a", "b", "i", "s")]


class Example10(Omit[Foo, ("a", "b")]):
    x: int

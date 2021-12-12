from typedpy import Array, DoNotSerialize, Structure, mappers


class Foo(Structure):
    i: int
    s: str
    _serialization_mapper = {"i": "j", "s": "name"}


class Example5(Foo):
    a: Array

    _serialization_mapper = [{"j": DoNotSerialize}, mappers.TO_LOWERCASE]
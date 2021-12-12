from typedpy import Array, FunctionCall, Structure, mappers


class Foo(Structure):
    xyz: Array
    i: int
    _serialization_mapper = {"i": "j"}


class Bar(Foo):
    a: Array

    _serialization_mapper = mappers.TO_LOWERCASE


class Example7(Bar):
    s: str
    foo: Foo
    _serialization_mapper = {}
    _deserialization_mapper = {"S": FunctionCall(func=lambda x: x * 2)}

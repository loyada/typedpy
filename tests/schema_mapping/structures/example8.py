from typedpy import Array, FunctionCall, Structure, mappers


class Foo(Structure):
    xyz: Array
    i: int
    _serialization_mapper = {"i": "j"}


class Bar(Foo):
    a: Array


class Example8(Bar):
    s: str
    foo: Foo
    _serialization_mapper = {"s": FunctionCall(func=lambda x: x * 2)}

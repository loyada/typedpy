from typedpy import Constant, Structure, mappers


class A(Structure):
    i: int

    _serialization_mapper = mappers.TO_LOWERCASE


class Example12(A):
    a: str
    _serialization_mapper = {"I": Constant(5), "A": "name"}

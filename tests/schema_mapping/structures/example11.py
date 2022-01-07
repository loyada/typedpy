import enum

from typedpy import Array, Enum, Structure


class Values(enum.Enum):
    AAA = 1
    BBB = 2
    CCC = 3


class Example11(Structure):
    many: Array[Enum(values=Values, serialization_by_value=True)]
    i: int

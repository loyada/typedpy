import enum

from typedpy import (
    Enum, Structure,
    AllOf,
    AnyOf,
    OneOf,
    Integer,
    String,
    Positive,
    Number,
    NotField,
)


class Foo(Structure):
    s = String


class Values(enum.Enum):
    one = enum.auto()
    two = enum.auto()
    three = enum.auto()


class Example(Structure):
    _additionalProperties = True
    _required = []
    a: AllOf([Number(multiplesOf=5, maximum=20, minimum=-10), Integer, Positive])
    # Can also omit the parens
    b: AnyOf[Number(maximum=20, minimum=-10), Integer(), Positive, String]
    c = OneOf(
        [Number(multiplesOf=5, maximum=20, minimum=-10), Integer, Positive, String]
    )
    d = NotField([Number(multiplesOf=5, maximum=20, minimum=-10), String])
    e = AllOf([])
    broken = AllOf[String, Integer]
    f = NotField[Number]
    g = AnyOf[Foo, Integer]
    values: Enum[Values]
    m: dict[str, Foo]

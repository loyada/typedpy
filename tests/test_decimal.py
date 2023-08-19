from decimal import Decimal
from json import dumps

from pytest import raises

from typedpy import (
    Deserializer,
    ImmutableStructure,
    NonNegative,
    Structure,
    Positive,
    DecimalNumber,
    serialize,
)


class PositiveDecimal(DecimalNumber, Positive):
    pass


class Foo(Structure):
    _required = []
    a = DecimalNumber
    b = DecimalNumber(maximum=100, multiplesOf=5)
    c = PositiveDecimal


def test_not_decimal_value():
    with raises(ValueError) as excinfo:
        Foo(a="1 1 ")
    assert "a: [<class 'decimal.ConversionSyntax'>]" in str(excinfo.value)


def test_not_decimal_type():
    with raises(TypeError) as excinfo:
        Foo(a={})
    assert "a: " in str(excinfo.value)


def test_basic_operation():
    f = Foo(a=Decimal("3.14"))
    assert f.a - 1 == Decimal("2.14")


def test_too_large():
    with raises(ValueError) as excinfo:
        Foo(b=1000)
    assert "b: Got 1000; Expected a maximum of 100" in str(excinfo.value)


def test_too_large2():
    f = Foo(b=90)
    with raises(ValueError) as excinfo:
        f.b += 20
    assert "b: Got 110; Expected a maximum of 100" in str(excinfo.value)


def test_not_multiple():
    with raises(ValueError) as excinfo:
        Foo(b=93)
    assert "b: Got 93; Expected a a multiple of 5" in str(excinfo.value)


def test_positivedecimal_err():
    with raises(ValueError) as excinfo:
        Foo(c=Decimal(-5))
    assert "c: Got -5; Expected a positive number" in str(excinfo.value)


def test_positivedecimal_valid():
    f = Foo(c=Decimal(5))
    assert int(f.c) == 5


def test_deserialize_string_as_decimal():
    f = Deserializer(Foo).deserialize({"c": "5"})
    assert int(f.c) == 5


class HasDecimal(ImmutableStructure):
    amount: NonNegative


def test_dump_decimal_field():
    has_decimal = HasDecimal(amount=Decimal("1.23"))
    assert dumps(serialize(has_decimal)) == '{"amount": "1.23"}'

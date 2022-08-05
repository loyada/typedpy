import sys

from pytest import fixture, raises
from typedpy import (
    Array,
    Deserializer,
    Negative,
    NegativeFloat,
    NegativeInt,
    NonNegative,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositive,
    NonPositiveFloat,
    NonPositiveInt,
    Positive,
    PositiveFloat,
    PositiveInt,
    Serializer,
    Structure,
    standard_readable_error_for_typedpy_exception,
)


class Foo(Structure):
    negative_int: NegativeInt
    negative_float: NegativeFloat
    negative: Array[Negative]

    positive_int: PositiveInt
    positive_float: PositiveFloat
    positive: Array[Positive]

    non_negative_int: NonNegativeInt
    non_negative_float: NonNegativeFloat
    non_negative: Array[NonNegative]

    non_positive_int: NonPositiveInt
    non_positive_float: NonPositiveFloat
    non_positive: Array[NonPositive]

    _required = []


def test_valid():
    original = {
        "negative_int": -1,
        "negative_float": -0.5,
        "negative": [-5],
        "positive_int": 1,
        "positive_float": 2.5,
        "positive": [10],
        "non_negative_int": 0,
        "non_negative_float": 0.5,
        "non_negative": [0, 0.5, 1],
        "non_positive_int": 0,
        "non_positive_float": -5.0,
        "non_positive": [-1, 0],
    }

    foo = Deserializer(Foo).deserialize(original)
    assert Serializer(foo).serialize() == original


@fixture(name="all_errors")
def fixture_all_errors():
    Structure.set_fail_fast(False)
    yield
    Structure.set_fail_fast(True)


def test_invalid_numbers(all_errors):

    original = {
        "negative_int": 0,
        "negative_float": -0,
        "negative": [-5, 5],
        "positive_int": 0,
        "positive_float": -1.5,
        "positive": [10, 1.0, 0],
        "non_negative_int": -1,
        "non_negative_float": -0.5,
        "non_negative": [0, 0.5, -1],
        "non_positive_int": 10,
        "non_positive_float": 5.0,
        "non_positive": [-1, 0, 1],
    }

    with raises(Exception) as ex:
        Foo(**original)
    errs = standard_readable_error_for_typedpy_exception(ex.value)
    assert len(errs) == 12
    err_fields = {err.field for err in errs}
    assert {
        "Foo.non_positive_2",
        "Foo.positive_2",
        "Foo.non_negative_2",
        "Foo.negative_1",
    } <= err_fields

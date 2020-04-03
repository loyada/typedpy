from decimal import Decimal

import pytest

from typedpy import StructureReference, Structure, String, Number, PositiveInt, Integer, create_typed_field


def test_wrapped_doesnt_need_named_param():
    class Wrapped(Structure):
        s = String

    assert Wrapped("abc").s == "abc"


class RangeCL(object):
    def __init__(self, min, max, step):
        self.min = min
        self.max = max
        self.step = step


def validate_range(range):
    if not isinstance(range.min, (float, int, Decimal)):
        raise TypeError()
    if range.min > range.max:
        raise ValueError()


ValidatedRangeField = create_typed_field("RangeField", RangeCL, validate_func=validate_range)


class Foo(Structure):
    r = ValidatedRangeField


def test_custom_typed_field_with_validation_valid():
    assert Foo(r=RangeCL(1, 10, 1)).r.min == 1


def test_custom_typed_field_with_validation_invalid():
    with pytest.raises(ValueError) as excinfo:
        Foo(r=RangeCL(11, 10, 1))


def test_validated_structure_as_field_invalid():
    class Range(Structure):
        min = Integer
        max = Integer
        step = Integer
        _required = ["min", "max"]

        def __validate__(self):
            if self.min > self.max:
                raise ValueError("min cannot be larger than max")

    class SomeApi(Structure):
        a = String
        r = Range

    with pytest.raises(ValueError):
        Range(min=10, max=1)
    with pytest.raises(ValueError):
        SomeApi(a="abc", r=Range(min=10, max=1))


def test_validated_structure_as_field_valid():
    class Range(Structure):
        min = Integer
        max = Integer
        step = Integer
        _required = ["min", "max"]

        def __validate__(self):
            if self.min > self.max:
                raise ValueError("min cannot be larger than max")

    class SomeApi(Structure):
        a = String
        r = Range

    assert Range(min=1, max=10).max == 10
    assert SomeApi(a="abc", r=Range(min=1, max=10)).r.min == 1

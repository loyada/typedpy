import enum

from pytest import raises

from typedpy import Enum, Positive, Structure, Array


class PositiveEnum(Enum, Positive): pass


class B(Structure):
    e = PositiveEnum[23, -5, 12, 5]


def test_not_positive_err():
    with raises(ValueError) as excinfo:
        B(e=-5)
    assert "e: Must be positive" in str(excinfo.value)


def test_not_valid_value_err():
    with raises(ValueError) as excinfo:
        B(e=10)
    assert "e: Must be one of [23, -5, 12, 5]" in str(excinfo.value)


def test_valid_value():
    assert B(e=23).e == 23


def test_valid_update():
    b = B(e=23)
    b.e = 12
    assert b.e == 12


def test_within_erray_err():
    class A(Structure):
        arr = Array(items=PositiveEnum(values=[23, -5, 12, 5]))

    with raises(ValueError) as excinfo:
        A(arr=[23, 5, 3, 5])
    assert "arr_2: Must be one of [23, -5, 12, 5]" in str(excinfo.value)


def test_enum_using_enum():
    class Values(enum.Enum):
        ABC = enum.auto()
        DEF = enum.auto()
        GHI = enum.auto()

    class Example(Structure):
        arr = Array[Enum[Values]]

    e = Example(arr=['ABC', Values.DEF, 'GHI'])
    assert e.arr == [Values.ABC, Values.DEF, Values.GHI]


def test_enum_using_enum_error():
    class Values(enum.Enum):
        ABC = enum.auto()
        DEF = enum.auto()
        GHI = enum.auto()

    class Example(Structure):
        arr = Array[Enum[Values]]

    with raises(ValueError) as excinfo:
        Example(arr = ['ABC', Values.DEF, 3])
    assert "arr_2: Must be a value of <enum 'Values'>" in str(excinfo.value)



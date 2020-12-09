import enum
import sys
import typing

import pytest
from pytest import raises

from typedpy import Structure, DecimalNumber, PositiveInt, String, Enum, Field, Integer, Map, Array, AnyOf, NoneField
from typedpy.structures import FinalStructure


class Venue(enum.Enum):
    NYSE = enum.auto()
    CBOT = enum.auto()
    AMEX = enum.auto()
    NASDAQ = enum.auto()


class Trader(Structure):
    lei: String(pattern='[0-9A-Z]{18}[0-9]{2}$')
    alias: String(maxLength=32)


def test_optional_fields():
    class Trade(Structure):
        notional: DecimalNumber(maximum=10000, minimum=0)
        quantity: PositiveInt(maximum=100000, multiplesOf=5)
        symbol: String(pattern='[A-Z]+$', maxLength=6)
        buyer: Trader
        seller: Trader
        venue: Enum[Venue]
        comment: String
        _optional = ["comment", "venue"]

    assert set(Trade._required) == {'notional', 'quantity', 'symbol', 'buyer', 'seller'}
    Trade(notional=1000, quantity=150, symbol="APPL",
          buyer=Trader(lei="12345678901234567890", alias="GSET"),
          seller=Trader(lei="12345678901234567888", alias="MSIM"),
          timestamp="01/30/20 05:35:35",
          )


def test_optional_fields_required_overrides():
    class Trade(Structure):
        notional: DecimalNumber(maximum=10000, minimum=0)
        quantity: PositiveInt(maximum=100000, multiplesOf=5)
        symbol: String(pattern='[A-Z]+$', maxLength=6)
        buyer: Trader
        seller: Trader
        venue: Enum[Venue]
        comment: String
        _optional = ["comment", "venue"]
        _required = []

    Trade()


def test_optional_fields_required_overrides1():
    class Trade(Structure):
        venue: Enum[Venue]
        comment: String
        _optional = ["venue"]
        _required = ["venue"]

    with raises(TypeError) as excinfo:
        Trade(comment="asdasd")
    assert "missing a required argument: 'venue'" in str(excinfo.value)


@pytest.fixture(scope="session")
def Point():
    from math import sqrt

    class PointClass:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def size(self):
            return sqrt(self.x ** 2 + self.y ** 2)

    return PointClass


def test_field_of_class(Point):
    class Foo(Structure):
        i: int
        point: Field[Point]

    foo = Foo(i=5, point=Point(3, 4))
    assert foo.point.size() == 5


def test_field_of_class_typeerror(Point):
    class Foo(Structure):
        i: int
        point: Field[Point]

    with raises(TypeError) as excinfo:
        Foo(i=5, point="xyz")
    assert "point: Expected <class 'test_structure.Point.<locals>.PointClass'>; Got 'xyz'" in str(
        excinfo.value)


def test_using_arbitrary_class_in_anyof(Point):
    class Foo(Structure):
        i: int
        point: AnyOf[Point, int]

    assert Foo(i=1, point = 2).point == 2


def test_using_arbitrary_class_in_union(Point):
    class Foo(Structure):
        i: int
        point: typing.Union[Point, int]

    assert Foo(i=1, point = 2).point == 2


def test_optional(Point):
    class Foo(Structure):
        i: int
        point: typing.Optional[Point]

    assert Foo(i=1).point is None
    assert Foo(i=1, point=None).point is None
    foo = Foo(i=1, point=Point(3,4))
    assert foo.point.size() == 5
    foo.point = None
    assert foo.point is None
    foo.point = Point(3,4)
    assert foo.point.size() == 5


def test_optional_err(Point):
    class Foo(Structure):
        i: int
        point: typing.Optional[Point]

    with raises(ValueError) as excinfo:
        Foo(i=1, point=3)
    assert "point: 3 Did not match any field option" in str(
            excinfo.value)


def test_field_of_class_in_map(Point):
    class Foo(Structure):
        i: int
        point_by_int: Map[Integer, Field[Point]]

    foo = Foo(i=5, point_by_int={1: Point(3, 4)})
    assert foo.point_by_int[1].size() == 5


def test_field_of_class_in_map_simpler_syntax(Point):
    class Foo(Structure):
        i: int
        point_by_int: Map[Integer, Point]

    foo = Foo(i=5, point_by_int={1: Point(3, 4)})
    assert foo.point_by_int[1].size() == 5


def test_field_of_class_in_map_typerror(Point):
    class Foo(Structure):
        i: int
        point_by_int: Map[Integer, Field[Point]]

    with raises(TypeError) as excinfo:
        Foo(i=5, point_by_int={1: Point(3, 4), 2: 3})
    assert "point_by_int_value: Expected <class 'test_structure.Point.<locals>.PointClass'>; Got 3" in str(
        excinfo.value)


def test_field_of_class_in_map__simpler_syntax_typerror(Point):
    class Foo(Structure):
        i: int
        point_by_int: Map[Integer, Point]

    with raises(TypeError) as excinfo:
        Foo(i=5, point_by_int={1: Point(3, 4), 2: 3})
    assert "point_by_int_value: Expected <class 'test_structure.Point.<locals>.PointClass'>; Got 3" in str(
        excinfo.value)

def test_simple_invalid_type():
    with raises(TypeError) as excinfo:
        class Foo(Structure):
            i = Array["x"]

    assert "Unsupported field type in definition: 'x'" in str(
        excinfo.value)


def test_simple_nonefield_usage():
    class Foo(Structure):
        a = Array[AnyOf[Integer, NoneField]]

    foo = Foo(a=[1,2,3, None, 4])
    assert foo.a == [1,2,3, None, 4]


def test_auto_none_conversion():
    class Foo(Structure):
        a = Array[AnyOf[Integer, None]]

    foo = Foo(a=[1,2,3, None, 4])
    assert foo.a == [1,2,3, None, 4]


def test_final_structure_violation():
    class Foo(FinalStructure):
        s: str

    with raises(TypeError) as excinfo:
        class Bar(Foo): pass
    assert "FinalStructure must not be extended. Tried to extend Foo" in str(
        excinfo.value)



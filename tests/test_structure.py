import enum
import sys
import typing
from dataclasses import dataclass
from datetime import datetime

import pytest
from pytest import raises

from typedpy import (
    FastSerializable,
    Serializer,
    Structure,
    DecimalNumber,
    PositiveInt,
    String,
    Enum,
    Field,
    Integer,
    Map,
    Array,
    AnyOf,
    NoneField,
    DateField,
    DateTime,
    AbstractStructure,
    FinalStructure,
    ImmutableStructure,
    unique, Undefined,
)

from typedpy.structures import MAX_NUMBER_OF_INSTANCES_TO_VERIFY_UNIQUENESS


class Venue(enum.Enum):
    NYSE = enum.auto()
    CBOT = enum.auto()
    AMEX = enum.auto()
    NASDAQ = enum.auto()


class Trader(Structure):
    lei: String(pattern="[0-9A-Z]{18}[0-9]{2}$")
    alias: String(maxLength=32)


def test_optional_fields():
    class Trade(Structure):
        notional: DecimalNumber(maximum=10000, minimum=0)
        quantity: PositiveInt(maximum=100000, multiplesOf=5)
        symbol: String(pattern="[A-Z]+$", maxLength=6)
        buyer: Trader
        seller: Trader
        venue: Enum[Venue]
        comment: String
        _optional = ["comment", "venue"]

    assert set(Trade._required) == {"notional", "quantity", "symbol", "buyer", "seller"}
    Trade(
        notional=1000,
        quantity=150,
        symbol="APPL",
        buyer=Trader(lei="12345678901234567890", alias="GSET"),
        seller=Trader(lei="12345678901234567888", alias="MSIM"),
        timestamp="01/30/20 05:35:35",
    )


def test_typing_optional_fields_none_allowed():
    class Trade(Structure):
        notional: DecimalNumber(maximum=10000, minimum=0)
        quantity: typing.Optional[PositiveInt]
        symbol: String(pattern="[A-Z]+$", maxLength=6)
        buyer: Trader
        seller: Trader
        venue: Enum[Venue]
        comment: String
        _required = []

    assert (
            Trade(
                notional=1000,
                quantity=None,
                symbol="AAA",
                buyer=Trader(lei="12345678901234567890", alias="GSET"),
                seller=Trader(lei="12345678901234567888", alias="MSIM"),
                timestamp="01/30/20 05:35:35",
            ).quantity
            is None
    )


def test_optional_fields_required_overrides():
    class Trade(Structure):
        notional: DecimalNumber(maximum=10000, minimum=0)
        quantity: PositiveInt(maximum=100000, multiplesOf=5)
        symbol: String(pattern="[A-Z]+$", maxLength=6)
        buyer: Trader
        seller: Trader
        venue: Enum[Venue]
        comment: String
        _optional = ["comment", "venue"]
        _required = []

    Trade()


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_field_by_name_fins_annotated_fields():
    class Trade(Structure):
        notional: DecimalNumber(maximum=10000, minimum=0)
        quantity: PositiveInt(maximum=100000, multiplesOf=5)
        symbol: String(pattern="[A-Z]+$", maxLength=6)
        buyer: Trader
        my_list: list[str]
        seller: typing.Optional[Trader]
        venue: Enum[Venue]
        comment: String
        _optional = ["comment", "venue"]
        _required = []

    field_names = Trade.get_all_fields_by_name().keys()
    for f in {"notional", "quantity", "seller", "symbol", "buyer", "my_list"}:
        assert f in field_names


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_iterating_over_wrapped_structure():
    class Foo(Structure):
        wrapped: list[str]
        _additionalProperties = False

    foo = Foo(wrapped=["x", "y", "z"])
    assert list(foo) == foo.wrapped


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_iterating_over_wrapped_structure_map():
    class Foo(Structure):
        wrapped: Map[str, int]
        _additionalProperties = False

    foo = Foo(wrapped={"x": 2, "y": 3, "z": 4})
    assert list(foo) == ["x", "y", "z"]


def test_cast():
    class Foo(Structure):
        a: int
        b: int

    class Bar(Foo, ImmutableStructure):
        s: typing.Optional[str]

    bar = Bar(a=1, b=2, s="xyz")
    foo: Foo = bar.cast_to(Foo)
    assert foo == Foo(a=1, b=2)
    assert foo.cast_to(Bar) == Bar(a=1, b=2)


def test_cast_invalid():
    class Foo(Structure):
        a: int
        b: int

    class Bar(Foo, ImmutableStructure):
        s: str

    foo = Foo(a=1, b=2)
    with raises(TypeError):
        foo.cast_to(Bar)
    with raises(TypeError):
        foo.cast_to(DateTime)


def test_iterating_over_wrapped_structure_err():
    class Foo(Structure):
        wrapped: int
        _additionalProperties = False

    foo = Foo(wrapped=4)
    with raises(TypeError) as excinfo:
        assert list(foo) == foo.wrapped
    assert "Foo is not a wrapper of an iterable" in str(excinfo.value)


def test_optional_fields_required_overrides1():
    with raises(ValueError) as excinfo:
        class Trade(Structure):
            venue: Enum[Venue]
            comment: String
            _optional = ["venue"]
            _required = ["venue"]

    assert (
            "optional cannot override prior required in the class or in a base class"
            in str(excinfo.value)
    )


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


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_optional_ignore_none(Point):
    class Foo(Structure):
        i: list[int]
        maybe_date: typing.Optional[DateField]
        _ignore_none = True

    assert Foo(i=[5], maybe_date=None).i == [5]
    assert Foo(i=[1]).maybe_date is None
    assert Foo(i=[1], maybe_date=None).i[0] == 1
    assert Foo(i=[5], maybe_date="2020-01-31").i[0] == 5
    with raises(ValueError):
        assert Foo(i=[5], maybe_date="2020-01-31a")


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_optional_global_config_ignore_none(Point, allow_none_for_optional):
    class Foo(Structure):
        i: list[int]
        maybe_date: DateField

        _required = []

    assert Foo(i=[5], maybe_date=None).i == [5]
    assert Foo(i=[1]).maybe_date is None
    assert Foo(i=[1], maybe_date=None).i[0] == 1
    assert Foo(i=[5], maybe_date="2020-01-31").i[0] == 5
    with raises(ValueError):
        assert Foo(i=[5], maybe_date="2020-01-31a")


def test_optional_do_not_ignore_none(Point):
    class Foo(Structure):
        i = Integer
        point: Field[Point]

        _required = []
        _ignore_none = False

    with raises(TypeError) as excinfo:
        Foo(i=None, point=Point(3, 4))
    assert ": Expected <class 'int'>; Got None" in str(excinfo.value)


def test_do_not_ignore_none_for_required_fields(Point):
    class Foo(Structure):
        i: int
        date: typing.Optional[DateField]
        _ignore_none = True

    with raises(TypeError) as excinfo:
        Foo(i=None)
    assert ": Expected <class 'int'>; Got None" in str(excinfo.value)


def test_field_of_class_typeerror(Point):
    class Foo(Structure):
        i: int
        point: Field[Point]

    with raises(TypeError) as excinfo:
        Foo(i=5, point="xyz")
    assert (
            "point: Expected <class 'tests.test_structure.Point.<locals>.PointClass'>; Got 'xyz'"
            in str(excinfo.value)
    )


def test_using_arbitrary_class_in_anyof(Point):
    class Foo(Structure):
        i: int
        point: AnyOf[Point, int]

    assert Foo(i=1, point=2).point == 2


def test_using_arbitrary_class_in_union(Point):
    class Foo(Structure):
        i: int
        point: typing.Union[Point, int]

    assert Foo(i=1, point=2).point == 2


def test_optional(Point):
    class Foo(Structure):
        i: int
        point: typing.Optional[Point]

    assert Foo(i=1).point is None
    assert Foo(i=1, point=None).point is None
    foo = Foo(i=1, point=Point(3, 4))
    assert foo.point.size() == 5
    foo.point = None
    assert foo.point is None
    foo.point = Point(3, 4)
    assert foo.point.size() == 5


def test_optional_err(Point):
    class Foo(Structure):
        i: int
        point: typing.Optional[Point]

    with raises(ValueError) as excinfo:
        Foo(i=1, point=3)
    assert (
            "Foo.point: 3 of type int did not match any field option. Valid types are: PointClass, None"
            in str(excinfo.value)
    )


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
    assert (
            "point_by_int_value: Expected <class 'tests.test_structure.Point.<locals>.PointClass'>; Got 3"
            in str(excinfo.value)
    )


def test_field_of_class_in_map__simpler_syntax_typerror(Point):
    class Foo(Structure):
        i: int
        point_by_int: Map[Integer, Point]

    with raises(TypeError) as excinfo:
        Foo(i=5, point_by_int={1: Point(3, 4), 2: 3})
    assert (
            "point_by_int_value: Expected <class 'tests.test_structure.Point.<locals>.PointClass'>; Got 3"
            in str(excinfo.value)
    )


def test_simple_invalid_type():
    with raises(TypeError) as excinfo:
        class Foo(Structure):
            i = Array["x"]

    assert "Unsupported field type in definition: 'x'" in str(excinfo.value)


def test_simple_nonefield_usage():
    class Foo(Structure):
        a = Array[AnyOf[Integer, NoneField]]

    foo = Foo(a=[1, 2, 3, None, 4])
    assert foo.a == [1, 2, 3, None, 4]


def test_auto_none_conversion():
    class Foo(Structure):
        a = Array[AnyOf[Integer, None]]

    foo = Foo(a=[1, 2, 3, None, 4])
    assert foo.a == [1, 2, 3, None, 4]


def test_final_structure_violation():
    class Foo(FinalStructure):
        s: str

    with raises(TypeError) as excinfo:
        class Bar(Foo):
            pass

    assert "Tried to extend Foo, which is a FinalStructure. This is forbidden" in str(
        excinfo.value
    )


def test_final_structure_no_violation():
    class Foo(Structure):
        s: str

    class Bar(Foo, FinalStructure):
        pass


def test_as_bool():
    class Foo(Structure):
        s: typing.Optional[str]
        i: typing.Optional[int]

    assert not (Foo())
    assert Foo(i=5)


def test_unique_violation(uniqueness_enabled):
    @unique
    class Foo(Structure):
        s: str
        i: int

    Foo(s="xxx", i=1)
    Foo(s="xxx", i=2)
    with raises(ValueError) as excinfo:
        Foo(s="xxx", i=1)
    assert (
            "Instance copy in Foo, which is defined as unique. Instance is"
            " <Instance of Foo. Properties: i = 1, s = 'xxx'>" in str(excinfo.value)
    )


def test_unique_violation_by_update(uniqueness_enabled):
    @unique
    class Foo(Structure):
        s: str
        i: int

    Foo(s="xxx", i=1)
    foo = Foo(s="xxx", i=2)
    with raises(ValueError) as excinfo:
        foo.i = 1
    assert (
            "Instance copy in Foo, which is defined as unique. Instance is"
            " <Instance of Foo. Properties: i = 1, s = 'xxx'>" in str(excinfo.value)
    )


def test_unique_violation_stop_checking__if_too_many_instances():
    @unique
    class Foo(Structure):
        i: int

    for i in range(MAX_NUMBER_OF_INSTANCES_TO_VERIFY_UNIQUENESS):
        Foo(i=i)
    Foo(i=1)
    Foo(i=1)


def test_copy_with_overrides():
    class Trade(Structure):
        notional: DecimalNumber(maximum=10000, minimum=0)
        quantity: PositiveInt(maximum=100000, multiplesOf=5)
        symbol: String(pattern="[A-Z]+$", maxLength=6)
        timestamp = DateTime
        buyer: Trader
        seller: Trader
        venue: Enum[Venue]
        comment: String
        _optional = ["comment", "venue"]

    trade_1 = Trade(
        notional=1000,
        quantity=150,
        symbol="APPL",
        buyer=Trader(lei="12345678901234567890", alias="GSET"),
        seller=Trader(lei="12345678901234567888", alias="MSIM"),
        timestamp="01/30/20 05:35:35",
    )
    trade_2 = trade_1.shallow_clone_with_overrides(notional=500)
    assert trade_2.notional == 500
    trade_2.notional = 1000
    assert trade_2 == trade_1


def test_defect_required_should_propagate_with_ignore_none():
    class Foo(Structure):
        a = Integer

    class Bar(Foo):
        s = String
        _ignore_none = True

    with raises(TypeError) as excinfo:
        Bar(s="x", a=None)
    assert "a: Expected <class 'int'>; Got None" in str(excinfo.value)


def test_defect_multiple_inheritance_with_optional_1():
    class Foo1(Structure):
        a = Integer(default=1)

    class Foo2(Structure):
        b = Integer

    class Bar1(Foo1, Foo2):
        pass

    class Bar2(Foo2, Foo1):
        pass

    Bar1(b=1)
    Bar2(b=1)


def test_defect_multiple_inheritance_with_optional_2():
    class Foo1(Structure):
        a = Integer
        _optional = ["a"]

    class Foo2(Structure):
        b = Integer

    class Bar1(Foo1, Foo2):
        pass

    class Bar2(Foo2, Foo1):
        pass

    Bar1(b=1)
    Bar2(b=1)


def test_from_other_class():
    class PersonModel:
        def __init__(self, *, first_name, age):
            self.first_name = first_name
            self.age = age

    class Person(Structure):
        id = Integer
        name = String
        age = Integer

    person_model = PersonModel(first_name="john", age=40)
    person = Person.from_other_class(person_model, id=123, name=person_model.first_name)
    assert person == Person(name="john", id=123, age=40)


def test_from_other_class_with_undefined():
    class PersonModel(Structure):
        id: int
        name: str
        age: int

        _required = []
        _enable_undefined_value = True

    class Person(Structure):
        id: int
        name: str
        age: int

        _required = []
        _ignore_none = []
        _enable_undefined_value = True

    person_model = PersonModel(age=40)
    assert Person.from_other_class(person_model, id=123) == Person(id=123, age=40)
    assert Person.from_other_class(person_model, id=Undefined) == Person(age=40)


def test_from_trusted_class():
    class PersonModel:
        def __init__(self, *, first_name, age):
            self.first_name = first_name
            self.age = age

    class Person(Structure, FastSerializable):
        id = Integer
        name = String
        age = Integer

    person_model = PersonModel(first_name="john", age=40)
    person = Person.from_trusted_data(
        person_model, id=123, name=person_model.first_name
    )
    assert person == Person(name="john", id=123, age=40)
    assert person.name == "john"
    assert Serializer(person).serialize() == {"name": "john", "age": 40, "id": 123}
    assert person.serialize() == {"name": "john", "age": 40, "id": 123}


def test_from_trusted_class_undefined():
    class PersonModel(Structure):
        id: int
        name: str
        age: int

        _required = []
        _enable_undefined_value = True

    class Person(Structure, FastSerializable):
        id: int
        name: str
        age: int

        _required = []
        _ignore_none = []
        _enable_undefined_value = True

    person_model = PersonModel(age=40)

    person = Person.from_trusted_data(
        person_model, id=123
    )
    assert person == Person(id=123, age=40)
    assert person.name is Undefined
    assert Serializer(person).serialize() == {"age": 40, "id": 123}
    assert person.serialize() == {"age": 40, "id": 123}

def test_from_trusted_dict():
    class PersonModel:
        def __init__(self, *, first_name, age):
            self.first_name = first_name
            self.age = age

    class Person(Structure, FastSerializable):
        id = Integer
        name = String
        age = Integer

    person_model = dict(first_name="john", age=40, id=123)

    person = Person.from_trusted_data(person_model, name=person_model["first_name"])
    assert person == Person(name="john", id=123, age=40)
    assert person.name == "john"
    assert Serializer(person).serialize() == {"name": "john", "age": 40, "id": 123}
    assert person.serialize() == {"name": "john", "age": 40, "id": 123}


def test_to_other_class():
    @dataclass
    class PersonDataclass:
        name: str
        age: int

    class Person(Structure):
        id = Integer
        name = String

    person = Person(id=1, name="john").to_other_class(
        PersonDataclass, ignore_props=["id"], age=40
    )
    assert person == PersonDataclass(name="john", age=40)


def test_defaults_are_connected_to_structure():
    class Foo(Structure):
        a: Array(items=String, default=list)

    foo = Foo()
    assert foo == Foo(a=[])
    assert foo.a == []
    foo.a.append("xyz")
    assert foo.a == ["xyz"]


def test_invalid_defaults_are_caught():
    def factory():
        return [1, 2, 3]

    with raises(TypeError) as excinfo:
        class Foo(Structure):
            a: Array(items=String, default=factory)

    assert "Invalid default value: [1, 2, 3];" in str(excinfo.value)


def test_default_alternative_style():
    def default_factory():
        return [1, 2, 3]

    class Example(Structure):
        i: Array[Integer] = default_factory

    assert Example() == Example(i=[1, 2, 3])


def test_inheritance_with_optional_field():
    class Foo(Structure):
        a: String
        b: String

    with raises(ValueError) as excinfo:
        class Bar(Foo):
            c: String

            _optional = ["b"]

    assert (
            "optional cannot override prior required in the class or in a base class"
            in str(excinfo.value)
    )


def test_classreference_cant_accept_none():
    class Foo(Structure):
        bar = String

    class Bar(Structure):
        bar = String
        foo = Foo

    with raises(TypeError) as excinfo:
        Bar(bar="abc", foo=None)
    assert (
            "foo: Expected <Structure: Foo. Properties: bar = <String>>; Got None"
            in str(excinfo.value)
    )


def test_required_is_inherited_field():
    class A(Structure):
        x = Integer
        y = Integer
        _required = []

    class B(A):
        _required = ["x", "y"]

    with raises(TypeError) as excinfo:
        B(y=5)
    assert "missing a required argument: 'x'" in str(excinfo.value)
    assert B(x=1, y=2).x == 1


def test_dont_allow_assignment_to_non_typedpy_types():
    Structure.set_block_non_typedpy_field_assignment()
    with raises(TypeError) as excinfo:
        class A(Structure):
            a = typing.List[str]

    assert "a: assigned a non-Typedpy type" in str(excinfo.value)
    with raises(TypeError) as excinfo:
        class B(Structure):
            b = typing.Optional[str]

    assert "b: assigned a non-Typedpy type" in str(excinfo.value)

    Structure.set_block_non_typedpy_field_assignment(False)

    class C(Structure):
        b = typing.List[str]


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_dont_allow_assignment_to_non_typedpy_types_pep585():
    Structure.set_block_non_typedpy_field_assignment()
    with raises(TypeError) as excinfo:
        class A(Structure):
            a = list[str]

    assert "a: assigned a non-Typedpy type" in str(excinfo.value)
    Structure.set_block_non_typedpy_field_assignment(False)

    class C(Structure):
        b = list[str]


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_dont_allow_assignment_to_non_typedpy_types_valid():
    Structure.set_block_non_typedpy_field_assignment()

    class A(Structure):
        a: list[str] = list

    assert A().a == []


def test_additional_properties_blocks_additional_properties_even_after_instantiation():
    class Foo(Structure):
        i: int
        _additionalProperties = False

    foo = Foo(i=5)
    with raises(ValueError) as excinfo:
        foo.x = []
    assert "Foo: trying to set a non-field 'x' is not allowed" in str(excinfo.value)


def test_additional_properties_blocks_additional_properties_even_after_instantiation1():
    class Foo(Structure):
        i: int
        _additional_properties = False

    foo = Foo(i=5)
    with raises(ValueError) as excinfo:
        foo.x = []
    assert "Foo: trying to set a non-field 'x' is not allowed" in str(excinfo.value)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_find_fields_with_function_returning_field():
    def Name() -> Field:
        return String(minLength=10)

    class Foo(Structure):
        age: int
        name: Name

    assert set(Foo.get_all_fields_by_name().keys()) == {"age", "name"}
    assert str(Foo.name) == "<String. Properties: minLength = 10>"


def test_disallow_mutable_default():
    with pytest.raises(ValueError) as excinfo:
        class Foo(Structure):
            a: list = []

    assert "use a generating function" in str(excinfo.value)


def test_abstract_structure():
    class Base(AbstractStructure):
        i: int

    class Foo(Base):
        a: str

    assert Foo(i=1, a="xyz").a == "xyz"
    with pytest.raises(TypeError) as excinfo:
        Base(i=1)
    assert "Not allowed to instantiate an abstract Structure" in str(excinfo.value)


def test_additional_props_default_false(additional_props_default_is_false):
    class Foo(Structure):
        a: str

    with pytest.raises(TypeError) as excinfo:
        Foo(a="x", b=1)
    assert "Foo: got an unexpected keyword argument 'b'" in str(excinfo.value)
    assert Foo(a="x").a == "x"


def test_auto_enum_conversion(auto_conversion_of_enums):
    class Color(enum.Enum):
        RED = 1
        GREEN = 2
        YELLOW = 3

    class Foo(Structure):
        color: Color

    foo = Foo(color=Color.RED)
    assert foo.color is Color.RED
    foo.color = Color.YELLOW  # no error
    with pytest.raises(ValueError) as excinfo:
        foo.color = 1
    assert "color: Got 1; Expected one of: RED, GREEN, YELLOW" in str(excinfo.value)


def test_issue_221():
    class Bar(ImmutableStructure):
        x: int

    Structure.set_additional_properties_default(False)

    # defect was that this class definition raises an exception
    class Foo(ImmutableStructure):
        a: int
        b: typing.Optional[int]
        c: bool = False

    Structure.set_additional_properties_default(True)


def test_eq_optional():
    class Foo(Structure):
        a: int = 5
        b: typing.Optional[int]

        _ignore_none = True

    assert Foo(a=5, b=None) == Foo()


def test_from_other_class_dict_is_suppoted():
    class Foo(Structure):
        i: int
        s: typing.Optional[str]
        dt: DateTime

    now = datetime.now()
    assert Foo.from_other_class({"i": 5, "dt": now}) == Foo(i=5, dt=now)


def test_from_other_class_err():
    class Foo(Structure):
        i: int

    with pytest.raises(TypeError) as excinfo:
        Foo.from_other_class(({"i": 5},))
    assert (
            "You provided an instance of <class 'tuple'>, that does not have all the required fields of Foo"
            in str(excinfo.value)
    )

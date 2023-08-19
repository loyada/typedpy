import enum
import sys
import time
import datetime
from datetime import date
from typing import Optional

import pytest

from typedpy import (
    Array,
    DateField,
    Deserializer,
    Extend,
    FastSerializable,
    FunctionCall,
    ImmutableStructure,
    PositiveInt,
    Set,
    create_serializer,
    mappers,
)
from typedpy.extfields import TimeField
from typedpy.structures import TypedPyDefaults
from typedpy.testing import assert_trusted_deserialization_mapper_is_safe


class Policy(ImmutableStructure, FastSerializable):
    soft_limit: PositiveInt
    hard_limit: PositiveInt
    time_days: Optional[PositiveInt]
    codes: Array[int]

    _ignore_none = True


create_serializer(Policy)


class Address(ImmutableStructure, FastSerializable):
    street_addr: str
    city: str
    zip: str


class Spend(ImmutableStructure, FastSerializable):
    day: int
    week: int
    month: int

    _required = []


class Role(enum.Enum):
    driver = 1
    admin = 2
    manager = 3


class Location(ImmutableStructure, FastSerializable):
    name: str
    id: int


class Policy(ImmutableStructure, FastSerializable):
    soft_limit: PositiveInt
    hard_limit: PositiveInt
    time_days: Optional[PositiveInt]
    codes: Array[int]


class Phone(ImmutableStructure, FastSerializable):
    number: str
    validated: bool


class Employee(Extend[Address], ImmutableStructure, FastSerializable):
    first_name: str
    last_name: str
    role: Role
    location: Location
    phone: Phone
    policies: Set[Policy]
    spend: Spend


# @timeit
def build_policies(**kw):
    return [Policy(soft_limit=x, **kw) for x in range(10, 10_000)]


# @timeit
def build_policies_fast(**kw):
    return [
        Policy.from_trusted_data(None, soft_limit=x, **kw) for x in range(10, 10_000)
    ]


def test_trusted_deserialization_equivalent_to_regular():
    # Given
    validated_policies = build_policies(hard_limit=20, codes=[1, 2, 3], time_days=7)
    serialized = [p.serialize() for p in validated_policies]
    deserializer = Deserializer(target_class=Policy)
    start = time.time()

    # When
    trusted_result = [
        deserializer.deserialize(input_data=i, direct_trusted_mapping=True)
        for i in serialized
    ]
    time_1 = time.time()
    untrusted_result = [deserializer.deserialize(input_data=i) for i in serialized]
    time_2 = time.time()

    # Then
    print(f"trusted serialization took: {time_1 - start}")
    print(f"untrusted serialization took: {time_2 - time_1}")
    print(f"ratio: {(time_2 - time_1) / (time_1 - start)}")
    assert trusted_result == untrusted_result


def test_serialize_with_enum():
    class LimitType(enum.Enum):
        one = 1
        two = 2
        three = 3

    class SpecialPolicy(Extend[Policy], ImmutableStructure, FastSerializable):
        limit_type: LimitType

        _required = []

    deserializer = Deserializer(target_class=SpecialPolicy)
    # Given
    validated_policies = build_policies(hard_limit=20, codes=[1, 2, 3], time_days=7)
    special_policies = [
        SpecialPolicy.from_other_class(x, limit_type=LimitType.two)
        for x in validated_policies
    ]
    special_policies.append(SpecialPolicy.from_other_class(validated_policies[0]))
    serialized = [p.serialize() for p in special_policies]
    start = time.time()

    # When
    trusted_result = [
        deserializer.deserialize(input_data=i, direct_trusted_mapping=True)
        for i in serialized
    ]
    time_1 = time.time()
    untrusted_result = [deserializer.deserialize(input_data=i) for i in serialized]
    time_2 = time.time()
    print(f"trusted serialization took: {time_1 - start}")
    print(f"untrusted serialization took: {time_2 - time_1}")
    print(f"ratio: {(time_2 - time_1) / (time_1 - start)}")
    assert trusted_result == untrusted_result


def create_employee() -> Employee:
    return Employee(
        first_name=f"joe-1",
        last_name="smith",
        role=Role.admin,
        location=Location(id=1, name="HQ"),
        zip="123123",
        city="ny",
        street_addr="100 w 45th",
        phone=Phone(number="917-1231231", validated=True),
        spend=Spend(
            day=10,
            week=50,
            month=200,
        ),
        policies={Policy(soft_limit=10, hard_limit=20, codes=[1, 2, 3])},
    )


def test_trusted_deserialize_nested_is_using_trusted_deserialization():
    employee = create_employee()
    serialized = employee.serialize()
    deserialized = Deserializer(target_class=Employee).deserialize(
        serialized, direct_trusted_mapping=True
    )

    # Then
    assert employee == deserialized
    # deserialized was created using "from_trusted_data"
    assert deserialized.used_trusted_instantiation()


def test_trusted_deserialization_with_mapper():
    class PolicyWithMapper(Extend[Policy], ImmutableStructure, FastSerializable):
        _serialization_mapper = mappers.TO_CAMELCASE

    deserializer = Deserializer(target_class=PolicyWithMapper)
    # Given
    validated_policies = build_policies(hard_limit=20, codes=[1, 2, 3], time_days=7)
    special_policies = [
        PolicyWithMapper.from_other_class(x) for x in validated_policies
    ]
    serialized = [p.serialize() for p in special_policies]
    start = time.time()

    # When
    trusted_result = [
        deserializer.deserialize(input_data=i, direct_trusted_mapping=True)
        for i in serialized
    ]
    time_1 = time.time()
    untrusted_result = [deserializer.deserialize(input_data=i) for i in serialized]
    time_2 = time.time()
    print(f"trusted serialization took: {time_1 - start}")
    print(f"untrusted serialization took: {time_2 - time_1}")
    print(f"ratio: {(time_2 - time_1) / (time_1 - start)}")
    assert trusted_result == untrusted_result


def test_trusted_deserialization_with_invalid_mapper():
    class PolicyWithMapper(ImmutableStructure):
        soft_limit: PositiveInt
        hard_limit: PositiveInt
        time_days: Optional[PositiveInt]
        codes: Array[int]

        _serialization_mapper = {"soft_limit": FunctionCall(func=lambda x: x * 100)}

    deserializer = Deserializer(target_class=PolicyWithMapper)
    # Given
    serialized = {"hard_limit": 5, "soft_limit": 4, "codes": [1, 2, 3]}
    deserializer.deserialize(input_data=serialized)

    # When/ Then
    with pytest.raises(ValueError) as excinfo:
        deserializer.deserialize(input_data=serialized, direct_trusted_mapping=True)
    assert "unsupported for trusted deserialization" in str(excinfo.value)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_nested_1():
    class Bar2(ImmutableStructure):
        b: int
        c: str

    class Bar1(ImmutableStructure):
        a: int
        bar2: list[Bar2]

    class Foo(ImmutableStructure):
        bar1: Bar1

    serialized = {
        "bar1": {"a": 5, "bar2": [{"b": 1, "c": "xyz"}, {"b": 2, "c": "abc"}]}
    }

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data=serialized, direct_trusted_mapping=True
    )
    assert deserialized == Foo(
        bar1=Bar1(a=5, bar2=[Bar2(b=1, c="xyz"), Bar2(b=2, c="abc")])
    )


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_nested_2():
    class Bar2(ImmutableStructure):
        b: int
        c: str

    class Bar1(ImmutableStructure):
        a: int
        bar2: Bar2

    class Foo(ImmutableStructure):
        bar1: Bar1

    serialized = {
        "bar1": {
            "a": 5,
            "bar2": {"b": 1, "c": "xyz"},
        }
    }

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data=serialized, direct_trusted_mapping=True
    )
    assert deserialized == Foo(bar1=Bar1(a=5, bar2=Bar2(b=1, c="xyz")))


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_nested_mapper_of_nested_class1():
    class Bar2(ImmutableStructure):
        b: int
        c: str

        _serialization_mapper = mappers.TO_LOWERCASE

    class Bar1(ImmutableStructure):
        a: int
        bar2: Bar2

        _serialization_mapper = mappers.TO_LOWERCASE

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    serialized = {
        "BAR1": {
            "a": 5,
            "bar2": {"B": 1, "C": "xyz"},
        }
    }

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data=serialized, direct_trusted_mapping=True
    )
    assert deserialized == Foo(bar1=Bar1(a=5, bar2=Bar2(b=1, c="xyz")))


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_nested_mapper_of_nested_class2():
    class Bar2(ImmutableStructure):
        b: int
        c: str

        _serialization_mapper = mappers.TO_LOWERCASE

    class Bar1(ImmutableStructure):
        a: int
        bar2: Bar2

    class Foo(ImmutableStructure):
        bar1: Bar1

    serialized = {
        "bar1": {
            "a": 5,
            "bar2": {"B": 1, "C": "xyz"},
        }
    }

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data=serialized, direct_trusted_mapping=True
    )
    assert deserialized == Foo(bar1=Bar1(a=5, bar2=Bar2(b=1, c="xyz")))


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_nested_mapper_of_nested_class3():
    class Bar2(ImmutableStructure):
        b_1: int
        c_1: str

        _serialization_mapper = mappers.TO_CAMELCASE

    class Bar1(ImmutableStructure):
        a: int
        bar2: list[Bar2]

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    serialized = {
        "BAR1": {"a": 5, "bar2": [{"b1": 1, "c1": "xyz"}, {"b1": 2, "c1": "abc"}]}
    }
    time_1 = time.time()
    for _ in range(1000):
        Deserializer(target_class=Foo).deserialize(input_data=serialized)
    time_2 = time.time()
    for _ in range(1000):
        deserialized = Deserializer(target_class=Foo).deserialize(
            input_data=serialized, direct_trusted_mapping=True
        )
    time_3 = time.time()

    print(f"ratio: {(time_2 - time_1) / (time_3 - time_2)}")

    assert deserialized == Foo(
        bar1=Bar1(a=5, bar2=[Bar2(b_1=1, c_1="xyz"), Bar2(b_1=2, c_1="abc")])
    )


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_nested_mapper_of_nested_class4():
    class Bar2(ImmutableStructure):
        b_1: int
        c_1: str

        _serialization_mapper = mappers.TO_CAMELCASE

    class Bar1(ImmutableStructure):
        a: int
        bar2: set[Bar2]

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    serialized = {
        "BAR1": {"a": 5, "bar2": [{"b1": 1, "c1": "xyz"}, {"b1": 2, "c1": "abc"}]}
    }

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data=serialized, direct_trusted_mapping=True
    )
    assert deserialized == Foo(
        bar1=Bar1(a=5, bar2={Bar2(b_1=1, c_1="xyz"), Bar2(b_1=2, c_1="abc")})
    )
    # deserialized was created using "from_trusted_data"
    assert deserialized.used_trusted_instantiation()


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_nested_mapper_of_nested_class5():
    class Bar1(ImmutableStructure):
        a: int
        bar2: set[str]

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    serialized = {"BAR1": {"a": 5, "bar2": ["aaa", "bbb", "aaa"]}}

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data=serialized, direct_trusted_mapping=True
    )
    assert deserialized == Foo(bar1=Bar1(a=5, bar2={"aaa", "bbb"}))
    # deserialized was created using "from_trusted_data"
    assert deserialized.used_trusted_instantiation()


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_nested_mapper_of_nested_class_datefield():
    class Bar1(ImmutableStructure):
        a: DateField
        d: set[DateField]

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    serialized = {"BAR1": {"a": "2022-01-30", "d": ["2023-07-30"]}}

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data=serialized, direct_trusted_mapping=True
    )
    assert deserialized == Foo(
        bar1=Bar1(
            a=date(year=2022, month=1, day=30), d={date(year=2023, month=7, day=30)}
        )
    )
    # deserialized was created using "from_trusted_data"
    assert deserialized.used_trusted_instantiation()


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_nested_mapper_of_nested_class_timefield():
    class Bar1(ImmutableStructure):
        a: datetime.time
        d: set[datetime.time]

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    serialized = {"BAR1": {"a": "7:1:15", "d": ["16:00:0"]}}

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data=serialized, direct_trusted_mapping=True
    )
    assert deserialized == Foo(
        bar1=Bar1(
            a=datetime.time(hour=7, minute=1, second=15),
            d={datetime.time(hour=16, minute=0, second=0)},
        )
    )
    # deserialized was created using "from_trusted_data"
    assert deserialized.used_trusted_instantiation()


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_safe_check_false_1():
    class Bar1(ImmutableStructure):
        a: datetime.time
        d: set[datetime.time]

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    with pytest.raises(AssertionError):
        assert_trusted_deserialization_mapper_is_safe(Foo)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_safe_check_corrected_1():
    class Bar1(ImmutableStructure):
        a: datetime.time
        d: set[datetime.time]

        _serialization_mapper = mappers.TO_LOWERCASE

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    assert_trusted_deserialization_mapper_is_safe(Foo)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_safe_check_false_2():
    class Bar2(ImmutableStructure):
        b_1: int
        c_1: str

        _serialization_mapper = mappers.TO_CAMELCASE

    class Bar1(ImmutableStructure):
        a: int
        bar2: set[Bar2]

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    with pytest.raises(AssertionError):
        assert_trusted_deserialization_mapper_is_safe(Foo)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_trusted_deserialization_safe_check_corrected_2():
    class Bar2(ImmutableStructure):
        b_1: int
        c_1: str

        _serialization_mapper = mappers.TO_CAMELCASE

    class Bar1(ImmutableStructure):
        a: int
        bar2: set[Bar2]

        _serialization_mapper = mappers.TO_LOWERCASE

    class Foo(ImmutableStructure):
        bar1: Bar1

        _serialization_mapper = mappers.TO_LOWERCASE

    assert_trusted_deserialization_mapper_is_safe(Foo)


def test_trusted_deserialization_safe_check_false_3():
    class Bar(ImmutableStructure):
        b_1: int
        c_1: str

        _serialization_mapper = [mappers.TO_CAMELCASE, mappers.TO_LOWERCASE]

    with pytest.raises(AssertionError):
        assert_trusted_deserialization_mapper_is_safe(Bar)


def test_trusted_deserialization_safe_check_false_3():
    class Bar(ImmutableStructure):
        b_1: int
        c_1: str

        _serialization_mapper = [mappers.TO_CAMELCASE, mappers.TO_LOWERCASE]

    with pytest.raises(AssertionError):
        assert_trusted_deserialization_mapper_is_safe(Bar)


def test_trusted_deserialization_safe_check_false_4():
    class Bar(ImmutableStructure):
        a: int

    class Foo(ImmutableStructure):
        bar1: Bar

        _serialization_mapper = {"bar1._mapper": {"a": "A"}}

    with pytest.raises(AssertionError):
        assert_trusted_deserialization_mapper_is_safe(Foo)


def test_trusted_deserialization_safe_check_corrected_4():
    class Bar(ImmutableStructure):
        a: int

    _serialization_mapper = {"a": "A"}

    class Foo(ImmutableStructure):
        bar1: Bar

        _serialization_mapper = {"bar1": "Foo"}

    assert_trusted_deserialization_mapper_is_safe(Foo)


def test_simple_enum():
    TypedPyDefaults.automatic_enum_conversion = True

    class Color(enum.Enum):
        red = 1
        black = 2
        green = 3

    class Foo1234(ImmutableStructure):
        c: Color

    deserialized = Deserializer(target_class=Foo1234).deserialize(
        input_data={"c": "red"}, direct_trusted_mapping=True
    )
    assert deserialized.used_trusted_instantiation()
    assert deserialized == Foo1234(c=Color.red)


def test_deserialize_optional():
    class Bar(ImmutableStructure):
        a: Optional[int]

    class Foo111(ImmutableStructure):
        i: Optional[int]
        b: Optional[Bar]

    assert_trusted_deserialization_mapper_is_safe(Foo111)

    deserialized = Deserializer(target_class=Foo111).deserialize(
        input_data={}, direct_trusted_mapping=True
    )
    assert deserialized.used_trusted_instantiation()
    assert deserialized == Foo111()

    deserialized = Deserializer(target_class=Foo111).deserialize(
        input_data={"b": {"a": 123}}, direct_trusted_mapping=True
    )
    assert deserialized.used_trusted_instantiation()
    assert deserialized == Foo111(b=Bar(a=123))

    deserialized = Deserializer(target_class=Foo111).deserialize(
        input_data={"b": {}, "i": 1}, direct_trusted_mapping=True
    )
    assert deserialized.used_trusted_instantiation()
    assert deserialized == Foo111(b=Bar(), i=1)


def test_serializablefield_with_simple_class():
    class Foo(ImmutableStructure):
        t: TimeField

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data={"t": "12:00:00"}, direct_trusted_mapping=True
    )
    assert deserialized.used_trusted_instantiation()
    assert deserialized == Foo(t=datetime.time(hour=12))


def test_deserialize_none1():
    class Foo(ImmutableStructure):
        t: int = 5
        i: Optional[int]

        _ignore_none = True

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data={"i": 4, "t": None}, direct_trusted_mapping=True
    )
    assert deserialized == Foo(t=5, i=4)


def test_deserialize_none2():
    class Foo(ImmutableStructure):
        t: int = 5
        i: Optional[int]

    deserialized = Deserializer(target_class=Foo).deserialize(
        input_data={"i": None}, direct_trusted_mapping=True
    )
    assert deserialized == Foo(t=5)

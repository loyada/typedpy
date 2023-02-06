import enum
import time
from typing import Optional

import pytest

from typedpy import (
    Array, Extend,
    FastSerializable,
    ImmutableStructure,
    PositiveInt,
    Set, create_serializer,
)


class Policy(ImmutableStructure, FastSerializable):
    soft_limit: PositiveInt
    hard_limit: PositiveInt
    time_days: Optional[PositiveInt]
    codes: Array[int]


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


def test_trusted_instantiation_equivalent_to_regular():
    start = time.time()
    validated_policies = build_policies(hard_limit=20, codes=[1, 2, 3], time_days=7)
    time_1 = time.time()
    fast_policies = build_policies_fast(hard_limit=20, codes=[1, 2, 3], time_days=7)
    time_2 = time.time()
    print(f"validated policies took: {time_1 - start}")
    print(f"fast policies took: {time_2 - time_1}")
    print(f"ratio: {(time_1 - start) / (time_2 - time_1)}")
    assert validated_policies == fast_policies


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
        policies={
            Policy(
                soft_limit=10, hard_limit=20, codes=[1, 2, 3]
            )
        },
    )


def create_trusted_employee() -> Employee:
    return Employee.from_trusted_data(
        None,
        first_name=f"joe-1",
        last_name="smith",
        role=Role.admin,
        location=Location.from_trusted_data(None, id=1, name="HQ"),
        zip="123123",
        city="ny",
        street_addr="100 w 45th",
        phone=Phone.from_trusted_data(None, number="917-1231231", validated=True),
        spend=Spend.from_trusted_data(
            None,
            day=10,
            week=50,
            month=200,
        ),
        policies={
            Policy.from_trusted_data(
                None, soft_limit=10, hard_limit=20, codes=[1, 2, 3]
            )
        },
    )


def test_nested_trusted_instantiation():
    employee = create_employee()
    trusted_employee = create_trusted_employee()
    assert employee == trusted_employee


def test_trusted_instantiation_different_style():
    start = time.time()
    validated_policies = build_policies(hard_limit=20, codes=[1, 2, 3], time_days=7)
    time_1 = time.time()
    Policy.trust_supplied_values(True)
    fast_policies = build_policies(hard_limit=20, codes=[1, 2, 3], time_days=7)
    time_2 = time.time()
    print(f"validated policies took: {time_1 - start}")
    print(f"fast policies took: {time_2 - time_1}")
    print(f"ratio: {(time_1 - start) / (time_2 - time_1)}")
    assert validated_policies == fast_policies


def test_nested_trusted_instantiation_with_dict():
    employee = create_employee()
    trusted_employee = Employee.from_trusted_data(employee.to_other_class(dict))
    assert employee == trusted_employee


def create_trusted_employee_missing_arg() -> Employee:
    return Employee.from_trusted_data(
        None,
        last_name="smith",
        role=Role.admin,
        location=Location.from_trusted_data(None, id=1, name="HQ"),
        zip="123123",
        city="ny",
        street_addr="100 w 45th",
        phone=Phone.from_trusted_data(None, number="917-1231231", validated=True),
        spend=Spend.from_trusted_data(
            None,
            day=10,
            week=50,
            month=200,
        ),
        policies={
            Policy.from_trusted_data(
                None, soft_limit=10, hard_limit=20, codes=[1, 2, 3]
            )
        },
    )


def test_trusted_invalid():
    employee = create_employee()

    # This is not validated, so does not raise exception
    trusted = employee.from_trusted_data(employee, last_name=None)

    # This is validated, so raises correct error
    with pytest.raises(TypeError) as excinfo:
        trusted.shallow_clone_with_overrides()
    assert "missing a required argument: 'last_name'" in str(excinfo.value)



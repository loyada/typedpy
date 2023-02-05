import enum
import time
from typing import Optional

from typedpy import Array, Deserializer, Extend, FastSerializable, ImmutableStructure, PositiveInt, Set, \
    create_serializer


class Policy(ImmutableStructure, FastSerializable):
    soft_limit: PositiveInt
    hard_limit: PositiveInt
    time_days: Optional[PositiveInt]
    mccs: Array[int]


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
    mccs: Array[int]


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
    return [Policy.from_trusted_data(None, soft_limit=x, **kw) for x in range(10, 10_000)]


def test_trusted_deserialization_equivalent_to_regular():
    # Given
    validated_policies = build_policies(hard_limit=20, mccs=[1, 2, 3], time_days=7)
    serialized = [p.serialize() for p in validated_policies]
    deserializer = Deserializer(target_class=Policy)
    start = time.time()

    # When
    trusted_result = [deserializer.deserialize(input_data=i, direct_trusted_mapping=True) for i in serialized]
    time_1 = time.time()
    untrusted_result = [deserializer.deserialize(input_data=i) for i in serialized]
    time_2 = time.time()

    # Then
    print(f"trusted serialization took: {time_1 - start}")
    print(f"untrusted serialization took: {time_2 - time_1}")
    print(f"ratio: { (time_2 - time_1) / (time_1 - start)}")
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
        policies={
            Policy(
                soft_limit=10, hard_limit=20, mccs=[1, 2, 3]
            )
        },
    )

def test_trusted_deserialize_nested_is_using_standard_deserialization():
    employee = create_employee()
    serialized = employee.serialize()
    deserialized = Deserializer(target_class=Employee).deserialize(serialized, direct_trusted_mapping=True)

    # Then
    assert employee == deserialized
    # deserialized was not created using "from_trusted_data"
    assert getattr(deserialized, "_trust_supplied_values", False) == False
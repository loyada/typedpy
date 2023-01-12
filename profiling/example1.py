import enum
import time
from functools import wraps
from typing import Optional

from typedpy import (
    ImmutableStructure,
    Extend,
    Serializer,
    Structure,
    PositiveInt,
    mappers,
)
from typedpy.serialization.fast_serialization import create_serializer
from typedpy.structures import TypedPyDefaults

Structure.set_auto_enum_conversion(True)


class Address(ImmutableStructure):
    street_addr: str
    city: str
    zip: str

    _serialization_mapper = mappers.TO_CAMELCASE


class Spend(ImmutableStructure):
    day: int
    week: int
    month: int

    _serialization_mapper = mappers.TO_CAMELCASE
    _required = []


class Role(enum.Enum):
    driver = 1
    admin = 2
    manager = 3


class Location(ImmutableStructure):
    name: str
    id: int


class Policy(ImmutableStructure):
    soft_limit: PositiveInt
    hard_limit: PositiveInt
    time_days: Optional[PositiveInt]
    mccs: list[int]

    _serialization_mapper = mappers.TO_CAMELCASE


class Phone(ImmutableStructure):
    number: str
    validated: bool


class Employee(Extend[Address], ImmutableStructure):
    first_name: str
    last_name: str
    role: Role
    location: Location
    phone: Phone
    policies: set[Policy]
    is_active: bool
    spend: Spend

    _serialization_mapper = mappers.TO_CAMELCASE


class Vehicle(ImmutableStructure):
    name: str
    license_plate: str
    location: Location
    is_active: bool
    policies: set[Policy]

    _serialization_mapper = mappers.TO_CAMELCASE


class Card(ImmutableStructure):
    company_id: str
    card_id: str

    _serialization_mapper = mappers.TO_CAMELCASE


class Assignment(ImmutableStructure):
    card: Card
    employee: Employee
    vehicle: Vehicle


class Firm(ImmutableStructure):
    name: str
    employees: list[Employee]
    vehicles: list[Vehicle]
    assignments: list[Assignment]
    cards: list[Card]
    spend: Spend
    credit: PositiveInt

    _serialization_mapper = mappers.TO_CAMELCASE

    def serialize1(self):
        return {
            "name": self.name,
            "employees": [Employee.serialize(e) for e in self.employees],
            "cards": [Card.serialize(c) for c in self.cards],
            "assignments": [Assignment.serialize(a) for a in self.assignments],
            "spend": Spend.serialize(self.spend),
            "credit": self.credit,
        }


def create_employees(fleet_id) -> list[Employee]:
    return [
        Employee(
            first_name=f"joe-{fleet_id}-{x}",
            last_name="smith",
            role=Role.admin,
            location=Location(id=x, name="HQ"),
            zip="123123",
            city="ny",
            street_addr="100 w 45th",
            phone=Phone(number="917-1231231", validated=True),
            is_active=(x % 2 == 0),
            spend=Spend(
                day=10,
                week=50,
                month=200,
            ),
            policies={Policy(soft_limit=10, hard_limit=20, mccs=[1, 2, 3])},
        )
        for x in range(100)
    ]


def create_vehicles(fleet_id) -> list[Vehicle]:
    return [
        Vehicle(
            name=f"vehicle-{fleet_id}-{x}",
            license_plate=f"{x}-123-{fleet_id}",
            location=Location(id=x, name="HQ"),
            is_active=True,
            policies={Policy(soft_limit=10, hard_limit=20, mccs=[1, 2, 3])},
        )
        for x in range(100)
    ]


def create_cards(fleet_id) -> list[Card]:
    return [Card(company_id=str(fleet_id), card_id=f"{x}") for x in range(100)]


def create_assignments(employees, vehicless, cards) -> list[Assignment]:
    return [
        Assignment(employee=e, vehicle=v, card=c)
        for (e, v, c) in zip(employees, vehicless, cards)
    ]


def create_spend(company_id) -> Spend:
    return Spend(day=company_id * 7, month=company_id * 5, week=company_id * 9)


def create_firm(company_id: int):
    employees = create_employees(company_id)
    vehicles = create_vehicles(company_id)
    cards = create_cards(company_id)
    assignments = create_assignments(employees, vehicles, cards)
    spend = create_spend(company_id)
    return Firm(
        name=f"firm-{company_id}",
        employees=employees,
        vehicles=vehicles,
        cards=cards,
        assignments=assignments,
        spend=spend,
        credit=50000,
    )


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f"Function {func.__name__} Took {total_time:.4f} seconds")
        return result

    return timeit_wrapper


@timeit
def create_many_firms(number: int) -> list[Firm]:
    return [create_firm(i) for i in range(number)]


@timeit
def serialize_all(the_firms: list[Firm]):
    return [Serializer(firm).serialize() for firm in the_firms]


@timeit
def serialize_all_optimized(firms: list[Firm]):
    return [Firm.serialize(f) for f in firms]


create_serializer(Firm)
create_serializer(Employee)
create_serializer(Vehicle)
create_serializer(Policy)
create_serializer(Spend)
create_serializer(Address)
create_serializer(Assignment)
create_serializer(Card)
create_serializer(Phone)
create_serializer(Location)


if __name__ == "__main__":
    firms = create_many_firms(50)
    import cProfile
    import pstats

    TypedPyDefaults.defensive_copy_on_get = False
    with cProfile.Profile() as pr:
        serialize_all_optimized(firms)
        # serialize_all(firms)
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    stats.dump_stats(filename="performance.prof")

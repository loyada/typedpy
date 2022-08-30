import enum
from typing import Optional

from typedpy import ImmutableStructure, Extend, Structure, PositiveInt

Structure.set_auto_enum_conversion(True)


class Address(ImmutableStructure):
    street_addr: str
    city: str
    zip: str


class Spend(ImmutableStructure):
    day: int
    week: int
    month: int

    _required = []

class Role(enum.Enum):
    driver = 1
    admin = 2
    manager = 3

class Location(ImmutableStructure):
    name: str
    id: str

class Policy(ImmutableStructure):
    soft_limit: PositiveInt
    hard_limit: PositiveInt
    time_days: Optional[PositiveInt]
    mccs: list[int]


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


class Vehicle(ImmutableStructure):
    name: str
    license_plate: str
    location: Location
    is_active: bool
    policies: set[Policy]



class Card(ImmutableStructure):
    company_id: str
    card_id: str


class Assignment(ImmutableStructure):
    card: Card
    employee: Employee
    vehicle: Vehicle


class Firm(ImmutableStructure):
    name: str
    employees: set[Employee]
    vehicle: set[Vehicle]
    assignments: set[Assignment]
    spend:Spend
    credit: PositiveInt


def create_employees(id) -> set[Employee]:
    pass


def create_vehicles(id) -> set[Vehicle]:
    pass


def create_cards(id) -> set[Card]:
     pass


def create_assignments(employees, vehicless, cards, id) -> set[Assignment]:
    pass


def create_spend(id) -> Spend:
    return Spend(day=id % 7, month=id % 5, week=id % 9)


def create_fleet(id: int):
    employees = create_employees(id)
    vehicles = create_vehicles(id)
    cards = create_cards(id)
    assignments = create_assignments(employees, vehicles, cards, id)
    spend = create_spend(id)
    return Firm(name=f"firm-{i}", employees=employees, vehicless=vehicles, cards=cards, assignments=assignments, spend=spend, credit=50000)

def create_many_fleets(number: int) -> list[Firm]:
    return [create_fleet(i) for i in range(number)]

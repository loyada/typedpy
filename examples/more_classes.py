from examples.enums import Sex
from typedpy import Enum, Structure


class Address(Structure):
    city: str
    zip: str


class Person(Structure):
    name: str
    age: int
    address: Address
    sex: Enum[Sex]



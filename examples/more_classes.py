from typedpy import Structure


class Address(Structure):
    city: str
    zip: str


class Person(Structure):
    name: str
    age: int
    address: Address


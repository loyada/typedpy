from examples.enums import Sex
from typedpy import Enum, Structure, create_pyi


class Address(Structure):
    city: str
    zip: str


class Person(Structure):
    name: str
    age: int
    address: Address
    sex: Enum[Sex]



if __name__ == "__main__":
    create_pyi(__file__, locals())




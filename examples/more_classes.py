import typing
from datetime import datetime

from examples.enums import Sex
from typedpy import Enum, Structure, create_pyi

CONSTANT1 = "some_name"
CONSTANT2 = {}

class Address(Structure):
    city: str
    zip: str


class Person(Structure):
    name: str
    age: int
    address: Address
    sex: Enum[Sex]


def aaa(*, a: dict[str, list[datetime]]) -> typing.Optional:
    pass

if __name__ == "__main__":
    create_pyi(__file__, locals())




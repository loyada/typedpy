import typing
from datetime import datetime
from os import path

from examples.enums import Sex
from typedpy import Enum, Structure, create_pyi

CONSTANT1 = "'some_name'"


class EmptyStruct(Structure):
    pass


class Address(Structure):
    city: str
    zip: str


CONSTANT2 = {Address: 123}


class Person(Structure):
    name: str
    age: int
    address: Address
    sex: Enum[Sex]


def aaa(*, a: dict[str, list[datetime]]) -> typing.Optional:
    pass


def bbb(p: path, d: typing.Dict):
    print(p)
    print(d)


if __name__ == "__main__":
    create_pyi(__file__, locals())

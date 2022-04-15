import enum
from typing import Union, Optional, Any
from typedpy import Structure

from examples.enums import Sex


class Address(Structure):
    def __init__(self, city: str,
        zip: str,
        **kw
    ): ...

    city: str
    zip: str


class Person(Structure):
    def __init__(self, name: str,
        age: int,
        address: Address,
        sex: Sex,
        **kw
    ): ...

    name: str
    age: int
    address: Address
    sex: Sex


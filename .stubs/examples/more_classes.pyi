
#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn
from typedpy import Structure
import enum

from datetime import datetime
from .enums import Sex



CONSTANT1 = None

CONSTANT2 = None

class Address(Structure):
    def __init__(
        self,
        city: str,
        zip: str,
        **kw
    ): ...

    city: str
    zip: str


class Person(Structure):
    def __init__(
        self,
        name: str,
        age: int,
        address: Address,
        sex: Sex,
        **kw
    ): ...

    name: str
    age: int
    address: Address
    sex: Sex


def aaa(*, a: dict[str, list[datetime]]) -> Optional: ...


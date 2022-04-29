
#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn
from typedpy import Structure

import typing
from datetime import datetime
from .enums import Sex



CONSTANT1 = 'some_name'

CONSTANT2 = {}

class Address(Structure):
    def __init__(
        self,
        city: str,
        zip: str,
        **kw
    ): ...

    def shallow_clone_with_overrides(
        self,
        city: str = None,
        zip: str = None,
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

    def shallow_clone_with_overrides(
        self,
        name: str = None,
        age: int = None,
        address: Address = None,
        sex: Sex = None,
        **kw
    ): ...

    name: str
    age: int
    address: Address
    sex: Sex


def aaa(*, a: dict[str, list[datetime]]) -> Optional: ...


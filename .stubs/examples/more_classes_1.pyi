
#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn, Iterable
from typedpy import Structure

import typing
from datetime import datetime as datetime
from functools import partial as partial
from os import path as path
from examples.enums import Sex as Sex
from typedpy import Enum as Enum
from typedpy import Structure as Structure
from typedpy import create_pyi as create_pyi


CONSTANT1: str = ""

CONSTANT2: dict = {}

BBB: partial

class NotStructure:
    pass



class MyException(Exception):
    pass



class FooException(MyException):
    pass



class EmptyStruct(Structure):
    pass

class Address(Structure):
    def __init__(
        self,
        city: str,
        zip: str
    ): ...

    def shallow_clone_with_overrides(
        self,
        city: str = None,
        zip: str = None
    ): ...

    @classmethod
    def from_other_class(
        cls,
        source_object: Any,
        *,
        ignore_props: Iterable[str] = None,
        city: str = None,
        zip: str = None
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
        *,
        ignore_props: Iterable[str] = None,
        city: str = None,
        zip: str = None
    ): ...


    city: str
    zip: str


class Person(Structure):
    def __init__(
        self,
        name: str,
        age: int,
        address: Address,
        sex: Sex
    ): ...

    def shallow_clone_with_overrides(
        self,
        name: str = None,
        age: int = None,
        address: Address = None,
        sex: Sex = None
    ): ...

    @classmethod
    def from_other_class(
        cls,
        source_object: Any,
        *,
        ignore_props: Iterable[str] = None,
        name: str = None,
        age: int = None,
        address: Address = None,
        sex: Sex = None
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
        *,
        ignore_props: Iterable[str] = None,
        name: str = None,
        age: int = None,
        address: Address = None,
        sex: Sex = None
    ): ...


    name: str
    age: int
    address: Address
    sex: Sex
    some_const: int
    not_struct: NotStructure


def aaa(*, a: dict[str, list[datetime]]) -> Optional: ...


def bbb(p: path, d: dict): ...


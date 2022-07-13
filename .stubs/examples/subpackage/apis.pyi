
#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn, Iterable
from typedpy import Structure

from datetime import datetime
from examples.more_classes import Person
from examples import Foo as Foo
from examples.enums import State as State
from typedpy import Enum as Enum
from typedpy import Extend as Extend
from typedpy import ImmutableStructure as ImmutableStructure
from typedpy import Partial as Partial
from typedpy import PositiveInt as PositiveInt
from typedpy import String as String
from typedpy import create_pyi as create_pyi


class Vehicle(Structure):
    def __init__(
        self,
        license_plate_state: State,
        odometer: int,
        alias: str,
        license_plate: str,
        **kw
    ): ...

    def shallow_clone_with_overrides(
        self,
        license_plate_state: State = None,
        odometer: int = None,
        alias: str = None,
        license_plate: str = None,
        **kw
    ): ...

    @classmethod
    def from_other_class(
        cls,
        source_object: Any,
        *,
        ignore_props: Iterable[str] = None,
        license_plate_state: State = None,
        odometer: int = None,
        alias: str = None,
        license_plate: str = None,
        **kw
    ): ...


    license_plate_state: State
    odometer: int
    alias: str
    license_plate: str


class AnotherFoo(Structure):
    def __init__(
        self,
        i: int,
        s: str,
        person: Person,
        dob: datetime,
        arr: list[str],
        union: Union[int,str],
        any: Any,
        a: set,
        b: set,
        another: str,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    def shallow_clone_with_overrides(
        self,
        i: int = None,
        s: str = None,
        person: Person = None,
        dob: datetime = None,
        arr: list[str] = None,
        union: Union[int,str] = None,
        any: Any = None,
        a: set = None,
        b: set = None,
        another: str = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    @classmethod
    def from_other_class(
        cls,
        source_object: Any,
        *,
        ignore_props: Iterable[str] = None,
        i: int = None,
        s: str = None,
        person: Person = None,
        dob: datetime = None,
        arr: list[str] = None,
        union: Union[int,str] = None,
        any: Any = None,
        a: set = None,
        b: set = None,
        another: str = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...


    i: int
    s: str
    person: Person
    dob: datetime
    arr: list[str]
    union: Union[int,str]
    any: Any
    a: set
    b: set
    another: str
    d: Optional[dict[str, int]] = None


class Vehicle2(Structure):
    def __init__(
        self,
        license_plate_state: Optional[State] = None,
        odometer: Optional[int] = None,
        alias: Optional[str] = None,
        license_plate: Optional[str] = None,
        **kw
    ): ...

    def shallow_clone_with_overrides(
        self,
        license_plate_state: Optional[State] = None,
        odometer: Optional[int] = None,
        alias: Optional[str] = None,
        license_plate: Optional[str] = None,
        **kw
    ): ...

    @classmethod
    def from_other_class(
        cls,
        source_object: Any,
        *,
        ignore_props: Iterable[str] = None,
        license_plate_state: Optional[State] = None,
        odometer: Optional[int] = None,
        alias: Optional[str] = None,
        license_plate: Optional[str] = None,
        **kw
    ): ...


    license_plate_state: Optional[State] = None
    odometer: Optional[int] = None
    alias: Optional[str] = None
    license_plate: Optional[str] = None


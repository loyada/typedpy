
#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Any, Type, NoReturn
from typedpy import Structure

from .enums import Sex
from .more_classes import Address
from datetime import datetime
import enum
import typing
from typing import Callable as Callable
from typing import Iterable as Iterable
from typing import Iterator as Iterator
from typing import Mapping as Mapping
from typing import Optional as Optional
from typing import TypeVar as TypeVar
from .enums import State as State
from .more_classes import CONSTANT1 as CONSTANT1
from .more_classes import Person as Person
from typedpy import AnyOf as AnyOf
from typedpy import Anything as Anything
from typedpy import DateTime as DateTime
from typedpy import Enum as Enum
from typedpy import Extend as Extend
from typedpy import Float as Float
from typedpy import ImmutableStructure as ImmutableStructure
from typedpy import Integer as Integer
from typedpy import Map as Map
from typedpy import Omit as Omit
from typedpy import Partial as Partial
from typedpy import Pick as Pick
from typedpy import Set as Set
from typedpy import Structure as Structure
from typedpy import default_factories as default_factories
from typedpy import mappers as mappers
from typedpy import create_pyi as create_pyi
import enum


T = TypeVar("T", int, str)

IMPORTED_CONST: str = ""

class State1(Enum):
    NY = enum.auto()
    NJ = enum.auto()
    AL = enum.auto()
    FL = enum.auto()




class FooFoo:

    
    def __init__(self, *, mapper: dict[str, Any] = dict, camel_case_convert: bool = None): ...


class WithCustomInit(Structure):

    def shallow_clone_with_overrides(
        self,
        i: int = None,
        s: str = None,
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
        **kw
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
        *,
        ignore_props: Iterable[str] = None,
        i: int = None,
        s: str = None,
        **kw
    ): ...


    i: int
    s: str
    
    def __init__(self): ...


class Employee(Structure):
    def __init__(
        self,
        name: str,
        age: int,
        address: Address,
        sex: Sex,
        ssid: str,
        **kw
    ): ...

    def shallow_clone_with_overrides(
        self,
        name: str = None,
        age: int = None,
        address: Address = None,
        sex: Sex = None,
        ssid: str = None,
        **kw
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
        sex: Sex = None,
        ssid: str = None,
        **kw
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
        sex: Sex = None,
        ssid: str = None,
        **kw
    ): ...


    name: str
    age: int
    address: Address
    sex: Sex
    ssid: str
    
    @property
    def prop1(self) -> list[str]: ...


class Blah(Structure):
    def __init__(
        self,
        i: int,
        s: str,
        person: Person,
        dob: datetime,
        arr: list[str],
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
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
        *,
        ignore_props: Iterable[str] = None,
        i: int = None,
        s: str = None,
        person: Person = None,
        dob: datetime = None,
        arr: list[str] = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...


    i: int
    s: str
    person: Person
    dob: datetime
    arr: list[str]
    d: Optional[dict[str, int]] = None


class Foo(Blah, Structure):
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
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
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
    d: Optional[dict[str, int]] = None
    
    def get_double_aa(self, x: Optional[int], p: Person = None) -> str: ...
    
    def doit(self): ...
    
    @staticmethod
    def aaa() -> str: ...


class FooPartial(Structure):
    def __init__(
        self,
        x: str,
        i: Optional[int] = None,
        d: Optional[dict[str, int]] = None,
        s: Optional[str] = None,
        person: Optional[Person] = None,
        dob: Optional[datetime] = None,
        arr: Optional[list[str]] = None,
        union: Optional[Union[int,str]] = None,
        any: Optional[Any] = None,
        a: Optional[set] = None,
        b: Optional[set] = None,
        **kw
    ): ...

    def shallow_clone_with_overrides(
        self,
        x: str = None,
        i: Optional[int] = None,
        d: Optional[dict[str, int]] = None,
        s: Optional[str] = None,
        person: Optional[Person] = None,
        dob: Optional[datetime] = None,
        arr: Optional[list[str]] = None,
        union: Optional[Union[int,str]] = None,
        any: Optional[Any] = None,
        a: Optional[set] = None,
        b: Optional[set] = None,
        **kw
    ): ...

    @classmethod
    def from_other_class(
        cls,
        source_object: Any,
        *,
        ignore_props: Iterable[str] = None,
        x: str = None,
        i: Optional[int] = None,
        d: Optional[dict[str, int]] = None,
        s: Optional[str] = None,
        person: Optional[Person] = None,
        dob: Optional[datetime] = None,
        arr: Optional[list[str]] = None,
        union: Optional[Union[int,str]] = None,
        any: Optional[Any] = None,
        a: Optional[set] = None,
        b: Optional[set] = None,
        **kw
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
        *,
        ignore_props: Iterable[str] = None,
        x: str = None,
        i: Optional[int] = None,
        d: Optional[dict[str, int]] = None,
        s: Optional[str] = None,
        person: Optional[Person] = None,
        dob: Optional[datetime] = None,
        arr: Optional[list[str]] = None,
        union: Optional[Union[int,str]] = None,
        any: Optional[Any] = None,
        a: Optional[set] = None,
        b: Optional[set] = None,
        **kw
    ): ...


    x: str
    i: Optional[int] = None
    d: Optional[dict[str, int]] = None
    s: Optional[str] = None
    person: Optional[Person] = None
    dob: Optional[datetime] = None
    arr: Optional[list[str]] = None
    union: Optional[Union[int,str]] = None
    any: Optional[Any] = None
    a: Optional[set] = None
    b: Optional[set] = None


class FooOmit(Structure):
    def __init__(
        self,
        i: int,
        s: str,
        person: Person,
        dob: datetime,
        arr: list[str],
        union: Union[int,str],
        any: Any,
        x: int,
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
        x: int = None,
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
        x: int = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
        *,
        ignore_props: Iterable[str] = None,
        i: int = None,
        s: str = None,
        person: Person = None,
        dob: datetime = None,
        arr: list[str] = None,
        union: Union[int,str] = None,
        any: Any = None,
        x: int = None,
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
    x: int
    d: Optional[dict[str, int]] = None


class FooPick(Structure):
    def __init__(
        self,
        a: set,
        xyz: float,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    def shallow_clone_with_overrides(
        self,
        a: set = None,
        xyz: float = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    @classmethod
    def from_other_class(
        cls,
        source_object: Any,
        *,
        ignore_props: Iterable[str] = None,
        a: set = None,
        xyz: float = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
        *,
        ignore_props: Iterable[str] = None,
        a: set = None,
        xyz: float = None,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...


    a: set
    xyz: float
    d: Optional[dict[str, int]] = None


class Bar(Structure):
    def __init__(
        self,
        i: int,
        s: str,
        person: Person,
        dob: datetime,
        arr: list[str],
        union: Union[int,str],
        any: Any,
        x: int,
        state: State,
        stats: list[int],
        states: list[State],
        d: Optional[dict[str, int]] = None,
        opt: Optional[float] = None
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
        x: int = None,
        state: State = None,
        stats: list[int] = None,
        states: list[State] = None,
        d: Optional[dict[str, int]] = None,
        opt: Optional[float] = None
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
        x: int = None,
        state: State = None,
        stats: list[int] = None,
        states: list[State] = None,
        d: Optional[dict[str, int]] = None,
        opt: Optional[float] = None
    ): ...

    @classmethod
    def from_trusted_data(
        cls,
        source_object: Any = None,
        *,
        ignore_props: Iterable[str] = None,
        i: int = None,
        s: str = None,
        person: Person = None,
        dob: datetime = None,
        arr: list[str] = None,
        union: Union[int,str] = None,
        any: Any = None,
        x: int = None,
        state: State = None,
        stats: list[int] = None,
        states: list[State] = None,
        d: Optional[dict[str, int]] = None,
        opt: Optional[float] = None
    ): ...


    i: int
    s: str
    person: Person
    dob: datetime
    arr: list[str]
    union: Union[int,str]
    any: Any
    x: int
    state: State
    stats: list[int]
    states: list[State]
    d: Optional[dict[str, int]] = None
    opt: Optional[float] = None


def func(x = None, *, e: Employee = None, **kw) -> Mapping[str, str]: ...


def func2(t: T) -> list[T]: ...


def bbb() -> Callable[[Bar,str], Iterable[Foo]]: ...


def ccc() -> Callable[[T], None]: ...


def ddd() -> list[int, str, ...]: ...


def eee(x: Optional[int] = None, arr: list[str] = list) -> Optional[int]: ...


def fff(c: Optional[Callable]) -> Iterator[str]: ...


def ggg() -> tuple: ...


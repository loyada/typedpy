
#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn
from typedpy import Structure

from .enums import Sex
from .more_classes import Address
from datetime import datetime
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import Mapping
import enum
import typing
from .enums import State
from .more_classes import Person


T = TypeVar("T")

CONSTANT1 = 'some_name'

IMPORTED_CONST: str = 'some_name'

class State1(enum.Enum):
    NY = enum.auto()
    NJ = enum.auto()
    AL = enum.auto()
    FL = enum.auto()




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

    name: str
    age: int
    address: Address
    sex: Sex
    ssid: str


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

    i: int
    s: str
    person: Person
    dob: datetime
    arr: list[str]
    d: Optional[dict[str, int]] = None


class Foo(Structure):
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


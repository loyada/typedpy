from typing import Union, Optional, Any
from typedpy import Structure
from examples.more_classes import Address
from datetime import datetime

from examples.enums import State
from examples.more_classes import Person

class Employee(Structure):
    def __init__(self, name: str,
        age: int,
        address: Address,
        ssid: str,
        **kw
    ): ...

    name: str
    age: int
    address: Address
    ssid: str


class Blah(Structure):
    def __init__(self, i: int,
        s: str,
        person: Person,
        dob: datetime,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    i: int
    s: str
    person: Person
    dob: datetime
    d: Optional[dict[str, int]] = None


class Foo(Structure):
    def __init__(self, i: int,
        s: str,
        person: Person,
        dob: datetime,
        union: Union[int,str],
        any: Any,
        a: set,
        b: set,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    i: int
    s: str
    person: Person
    dob: datetime
    union: Union[int,str]
    any: Any
    a: set
    b: set
    d: Optional[dict[str, int]] = None
    
    def doit(self): ...
    
    def get_double_aa(self, x: int, p: Person = None) -> str: ...


class FooPartial(Structure):
    def __init__(self, x: str,
        i: Optional[int] = None,
        d: Optional[dict[str, int]] = None,
        s: Optional[str] = None,
        person: Optional[Person] = None,
        dob: Optional[datetime] = None,
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
    union: Optional[Union[int,str]] = None
    any: Optional[Any] = None
    a: Optional[set] = None
    b: Optional[set] = None


class FooOmit(Structure):
    def __init__(self, i: int,
        s: str,
        person: Person,
        dob: datetime,
        union: Union[int,str],
        any: Any,
        x: int,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    i: int
    s: str
    person: Person
    dob: datetime
    union: Union[int,str]
    any: Any
    x: int
    d: Optional[dict[str, int]] = None


class FooPick(Structure):
    def __init__(self, a: set,
        xyz: float,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    a: set
    xyz: float
    d: Optional[dict[str, int]] = None


class Bar(Structure):
    def __init__(self, i: int,
        s: str,
        person: Person,
        dob: datetime,
        union: Union[int,str],
        any: Any,
        x: int,
        state: State,
        d: Optional[dict[str, int]] = None,
        opt: Optional[float] = None,
        **kw
    ): ...

    i: int
    s: str
    person: Person
    dob: datetime
    union: Union[int,str]
    any: Any
    x: int
    state: State
    d: Optional[dict[str, int]] = None
    opt: Optional[float] = None


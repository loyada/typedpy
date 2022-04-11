from typedpy import Structure
from typing import Union, Optional, Any

from examples.enums import State
from examples.more_classes import Person

class Blah(Structure):
    def __init__(self, i: int,
        d: Optional[dict[str, int]],
        s: str,
        person: Person,
        **kw
    ): ...

    i: int
    d: Optional[dict[str, int]]
    s: str
    person: Person


class Foo(Structure):
    def __init__(self, i: int,
        d: Optional[dict[str, int]],
        s: str,
        person: Person,
        union: Union[int,str],
        any: Any,
        a: set,
        b: set,
        **kw
    ): ...

    i: int
    d: Optional[dict[str, int]]
    s: str
    person: Person
    union: Union[int,str]
    any: Any
    a: set
    b: set


class FooPartial(Structure):
    def __init__(self, i: Optional[int],
        d: Optional[dict[str, int]],
        s: Optional[str],
        person: Optional[Person],
        union: Optional[Union[int,str]],
        any: Optional[Any],
        a: Optional[set],
        b: Optional[set],
        x: str,
        **kw
    ): ...

    i: Optional[int]
    d: Optional[dict[str, int]]
    s: Optional[str]
    person: Optional[Person]
    union: Optional[Union[int,str]]
    any: Optional[Any]
    a: Optional[set]
    b: Optional[set]
    x: str


class FooOmit(Structure):
    def __init__(self, i: int,
        d: Optional[dict[str, int]],
        s: str,
        person: Person,
        union: Union[int,str],
        any: Any,
        x: int,
        **kw
    ): ...

    i: int
    d: Optional[dict[str, int]]
    s: str
    person: Person
    union: Union[int,str]
    any: Any
    x: int


class FooPick(Structure):
    def __init__(self, d: Optional[dict[str, int]],
        a: set,
        xyz: float,
        **kw
    ): ...

    d: Optional[dict[str, int]]
    a: set
    xyz: float


class Bar(Structure):
    def __init__(self, i: int,
        d: Optional[dict[str, int]],
        s: str,
        person: Person,
        union: Union[int,str],
        any: Any,
        x: int,
        opt: Optional[float],
        state: State,
        **kw
    ): ...

    i: int
    d: Optional[dict[str, int]]
    s: str
    person: Person
    union: Union[int,str]
    any: Any
    x: int
    opt: Optional[float]
    state: State


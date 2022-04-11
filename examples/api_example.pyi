from typedpy import Structure
from typing import Union, Optional, Any

from examples.enums import State
from examples.more_classes import Person

class Blah(Structure):
    def __init__(self, i: int,
        s: str,
        person: Person,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    i: int
    s: str
    person: Person
    d: Optional[dict[str, int]] = None


class Foo(Structure):
    def __init__(self, i: int,
        s: str,
        person: Person,
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
    union: Union[int,str]
    any: Any
    a: set
    b: set
    d: Optional[dict[str, int]] = None


class FooPartial(Structure):
    def __init__(self, x: str,
        i: Optional[int] = None,
        d: Optional[dict[str, int]] = None,
        s: Optional[str] = None,
        person: Optional[Person] = None,
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
    union: Optional[Union[int,str]] = None
    any: Optional[Any] = None
    a: Optional[set] = None
    b: Optional[set] = None


class FooOmit(Structure):
    def __init__(self, i: int,
        s: str,
        person: Person,
        union: Union[int,str],
        any: Any,
        x: int,
        d: Optional[dict[str, int]] = None,
        **kw
    ): ...

    i: int
    s: str
    person: Person
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
    union: Union[int,str]
    any: Any
    x: int
    state: State
    d: Optional[dict[str, int]] = None
    opt: Optional[float] = None


from typedpy import Structure
from typing import Union, Optional, Any

class Blah(Structure):
    def __init__(self, i: int,
        d: Optional[dict[str, int]],
        s: str,
        **kw
    ): ...

    i: int
    d: Optional[dict[str, int]]
    s: str


class Foo(Structure):
    def __init__(self, i: int,
        d: Optional[dict[str, int]],
        s: str,
        union: Union[int,str],
        any: Any,
        a: set,
        b: set,
        **kw
    ): ...

    i: int
    d: Optional[dict[str, int]]
    s: str
    union: Union[int,str]
    any: Any
    a: set
    b: set


class FooPartial(Structure):
    def __init__(self, i: Optional[int],
        d: Optional[dict[str, int]],
        s: Optional[str],
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
    union: Optional[Union[int,str]]
    any: Optional[Any]
    a: Optional[set]
    b: Optional[set]
    x: str


class FooOmit(Structure):
    def __init__(self, i: int,
        d: Optional[dict[str, int]],
        s: str,
        union: Union[int,str],
        any: Any,
        x: int,
        **kw
    ): ...

    i: int
    d: Optional[dict[str, int]]
    s: str
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
    union: Union[int,str]
    any: Any
    x: int
    opt: Optional[float]
    state: State


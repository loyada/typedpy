from typedpy import Structure

class Blah(Structure):
    i: int
    d: dict
    s: str


class Foo(Structure):
    i: int
    d: dict
    s: str
    a: set
    b: set


class FooPartial(Structure):
    i: int
    d: dict
    s: str
    a: set
    b: set
    x: str


class FooOmit(Structure):
    i: int
    d: dict
    s: str
    x: int


class FooPick(Structure):
    d: dict
    a: set
    xyz: float


from typedpy import ImmutableStructure, Structure
from typedpy.structures import Partial


class Foo(ImmutableStructure):
    i: int
    d: dict[str, int]
    s: str
    a: set


# noinspection PyUnresolvedReferences
def test_partial_of_structure():
    class Bar(Partial[Foo]):
        x: str

    assert Bar._required == ["x"]
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(i=5, x="xyz")
    assert bar.i == 5
    assert bar.s is None
    assert bar.x == "xyz"



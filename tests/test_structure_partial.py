import pytest

from typedpy import ImmutableStructure, Map, Structure, mappers, Serializer
from typedpy.structures import Partial


class Foo(ImmutableStructure):
    i: int
    d: Map[str, int] = dict
    s: str
    a: set

    _serialization_mapper = mappers.TO_LOWERCASE


# noinspection PyUnresolvedReferences
def test_partial_of_structure():
    class Bar(Partial[Foo]):
        x: str

    assert Bar._required == ["x"]
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(i=5, x="xyz")
    assert bar.d == {}
    bar.d = {"x": 1}

    assert bar.i == 5
    assert bar.s is None
    assert bar.x == "xyz"
    assert bar.d["x"] == 1
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)
    assert Serializer(bar).serialize() == {'D': {'x': 1}, 'I': 5, 'X': 'xyz'}

    Bar._serialization_mapper = {"I": "number"}
    assert Serializer(bar).serialize() == {'D': {'x': 1}, 'number': 5, 'X': 'xyz'}


def test_direct_assignment_to_partial():
    Bar = Partial[Foo]
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(i=5, a={1,2})
    assert bar.i == 5
    assert bar.s is None
    assert bar.a == {2,1}
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)


def test_direct_assignment_to_partial_with_class_name():
    Bar = Partial[Foo, "Bar"]
    assert Bar.__name__ == "Bar"


def test_partial_immutable():
    class Bar(Partial[Foo], ImmutableStructure):
        x: str

    bar = Bar(i=5, x="xyz")
    with pytest.raises(ValueError) as excinfo:
        bar.d = {}
    assert "Bar: Structure is immutable" in str(excinfo.value)



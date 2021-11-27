import pytest

from typedpy import ImmutableStructure, Integer, Map, Serializer, Structure, mappers


def build_default_dict():
    return {"abc": 0}


class Foo(ImmutableStructure):
    i: int
    d: Map[str, int] = build_default_dict
    s: set
    a: str
    b: Integer

    _serialization_mapper = mappers.TO_LOWERCASE


def test_omit_and_construct():
    class Bar(Foo.omit("a", "b")):
        x: int

    assert set(Bar._required) == {"i", "s", "x"}
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(i=5, x=10, s={1, 2, 3})
    assert bar.d == {"abc": 0}
    bar.d = {"x": 1}

    assert bar.i == 5
    assert bar.s == {1, 2, 3}
    assert bar.x == 10
    assert bar.d["x"] == 1
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)
    assert Serializer(bar).serialize() == {'D': {'x': 1}, 'I': 5, 'S': [1, 2, 3], 'X': 10}

    Bar._serialization_mapper = {"I": "number", "X": "xxx"}
    assert Serializer(bar).serialize() == {'D': {'x': 1}, 'number': 5, 'S': [1, 2, 3], 'xxx': 10}


def test_direct_assignment_to_omit():
    Bar = Foo.omit("a", "b", "i", "s")
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(d={"a": 5})
    assert Bar._required == []
    assert set(Bar.get_all_fields_by_name().keys()) == {"d"}
    assert bar.d == {"a": 5}
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)


def test_partial_immutable():
    class Bar(Foo.omit("a", "b"), ImmutableStructure):
        x: str

    bar = Bar(i=5, x="xyz", s= {1,2,3})
    with pytest.raises(ValueError) as excinfo:
        bar.d = {}
    assert "Bar: Structure is immutable" in str(excinfo.value)



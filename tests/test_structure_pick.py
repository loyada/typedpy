import pytest

from typedpy import ImmutableStructure, Integer, Map, Serializer, Structure, mappers, Pick


def build_default_dict():
    return {"abc": 0}


class Foo(ImmutableStructure):
    i: int
    d: Map[str, int] = build_default_dict
    s: set
    a: str
    b: Integer

    _serialization_mapper = mappers.TO_LOWERCASE


class Bar1(Foo.pick("a", "b", "d")):
    x: int


class Bar2(Pick[Foo, ("a", "b", "d")]):
    x: int


@pytest.mark.parametrize("Bar", [Bar1, Bar2], ids=["Structure.pick", "Pick[Structure]"])
def test_pick_and_construct(Bar):
    assert set(Bar._required) == {"a", "b", "x"}
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(a="a", x=10, b=5)
    assert bar.d == {"abc": 0}
    bar.d = {"x": 1}
    assert bar.a == "a"
    assert bar.b == 5
    assert bar.x == 10
    assert bar.d["x"] == 1
    assert bar == Bar(a="a", b=5, x=10, d={"x": 1})
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)
    assert Serializer(bar).serialize() == {'D': {'x': 1}, 'B': 5, 'A': "a", "X": 10}

    Bar._serialization_mapper = {"A": "ABC", "X": "xxx"}
    assert Serializer(bar).serialize() == {'D': {'x': 1}, 'ABC': "a", "B": 5, 'xxx': 10}


Bar3 = Foo.pick("d")

Bar4 = Pick[Foo, ("d",)]


@pytest.mark.parametrize("Bar", [Bar3, Bar4], ids=["Structure.pick", "Pick[Structure]"])
def test_direct_assignment_to_pick(Bar):
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(d={"a": 5})
    assert Bar._required == []
    assert set(Bar.get_all_fields_by_name().keys()) == {"d"}
    assert bar.d == {"a": 5}
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)
    assert Bar.__name__ == "PickFoo"


Bar5 = Foo.pick("d", class_name="Bar")

Bar6 = Pick[Foo, ("d",), "Bar"]


@pytest.mark.parametrize("Bar", [Bar5, Bar6], ids=["Structure.pick", "Pick[Structure]"])
def test_direct_assignment_to_pixk_with_class_name(Bar):
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    Bar(d={"a": 5})
    assert Bar.__name__ == "Bar"


def test_pick_immutable():
    class Bar(Pick[Foo, ("d", "s", "i")], ImmutableStructure):
        x: str

    bar = Bar(i=5, x="xyz", s= {1,2,3})
    with pytest.raises(ValueError) as excinfo:
        bar.d = {}
    assert "Bar: Structure is immutable" in str(excinfo.value)

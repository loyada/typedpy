import pytest

from typedpy import (
    ImmutableStructure,
    Integer,
    Map,
    Omit,
    Serializer,
    Structure,
    mappers,
)
from typedpy.serialization.mappers import aggregated_mapper_by_class


def build_default_dict():
    return {"abc": 0}


class Blah(Structure):
    i: int
    d: Map[str, int] = build_default_dict
    a: str


class Foo(Blah, ImmutableStructure):
    s: set
    b: Integer

    _serialization_mapper = mappers.TO_LOWERCASE


class Bar1(Foo.omit("a", "b")):
    x: int

    _serialization_mapper = Foo.get_aggregated_serialization_mapper()


class Bar2(Omit[Foo, ("a", "b")]):
    x: int

    _serialization_mapper = Foo.get_aggregated_serialization_mapper()


@pytest.mark.parametrize("Bar", [Bar1, Bar2], ids=["Structure.omit", "Omit[Structure]"])
def test_omit_and_construct(Bar):
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
    assert Serializer(bar).serialize() == {
        "D": {"x": 1},
        "I": 5,
        "S": [1, 2, 3],
        "X": 10,
    }

    Bar._serialization_mapper.append({"I": "number", "X": "xxx"})
    aggregated_mapper_by_class.clear()
    assert Serializer(bar).serialize() == {
        "D": {"x": 1},
        "number": 5,
        "S": [1, 2, 3],
        "xxx": 10,
    }


Bar3 = Foo.omit("a", "b", "i", "s")

Bar4 = Omit[Foo, ("a", "b", "i", "s")]


@pytest.mark.parametrize("Bar", [Bar3, Bar4], ids=["Structure.omit", "Omit[Structure]"])
def test_direct_assignment_to_omit(Bar):
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(d={"a": 5})
    assert Bar._required == []
    assert set(Bar.get_all_fields_by_name().keys()) == {"d"}
    assert bar.d == {"a": 5}
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)
    assert Bar.__name__ == "OmitFoo"


Bar5 = Foo.omit("a", "b", "i", "s", class_name="Bar")

Bar6 = Omit[Foo, ("a", "b", "i", "s"), "Bar"]


@pytest.mark.parametrize("Bar", [Bar5, Bar6], ids=["Structure.omit", "Omit[Structure]"])
def test_direct_assignment_to_omit_with_class_name(Bar):
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    Bar(d={"a": 5})
    assert Bar.__name__ == "Bar"


def test_omit_immutable():
    class Bar(Foo.omit("a", "b"), ImmutableStructure):
        x: str

    bar = Bar(i=5, x="xyz", s={1, 2, 3})
    with pytest.raises(ValueError) as excinfo:
        bar.d = {}
    assert "Bar: Structure is immutable" in str(excinfo.value)


def test_omit_additional_props_default_false(additional_props_default_is_false):
    class BarImmutable(Foo.omit("a", "b"), ImmutableStructure):
        x: str

    with pytest.raises(TypeError) as excinfo:
        BarImmutable(i=5, x="xyz", s={1, 2, 3}, qweasd=1)
    assert "BarImmutable: got an unexpected keyword argument 'qweasd'" in str(
        excinfo.value
    )

    class Bar(Foo.omit("a", "b"), Structure):
        x: str

    with pytest.raises(TypeError) as excinfo:
        Bar(i=5, x="xyz", s={1, 2, 3}, qweasd=1)
    assert "Bar: got an unexpected keyword argument 'qweasd'" in str(excinfo.value)

    assert BarImmutable(i=5, x="xyz", s={1, 2, 3}).x == "xyz"


def test_block_omit_with_wrong_field():
    with pytest.raises(TypeError) as excinfo:

        class Bar(Omit[Foo, ("a", "x")]):
            pass

    assert "Omit: 'x' is not a field of Foo" in str(excinfo.value)

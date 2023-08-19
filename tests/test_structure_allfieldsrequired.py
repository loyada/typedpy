import pytest

from typedpy import (
    ImmutableStructure,
    Map,
    Structure,
    mappers,
    Serializer,
    AllFieldsRequired,
)
from typedpy.serialization.mappers import aggregated_mapper_by_class


class Blah(Structure):
    i: int
    d: Map[str, int] = dict
    s: str


class Foo(Blah, ImmutableStructure):
    a: set

    _serialization_mapper = mappers.TO_LOWERCASE


# noinspection PyUnresolvedReferences
def test_allfieldsrequired_of_structure():
    class Bar(AllFieldsRequired[Foo]):
        x: str

        _serialization_mapper = Foo.get_aggregated_serialization_mapper()

    assert set(Bar._required) == {"x", "i", "s", "a"}
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(i=5, x="xyz", a={1, 2, 3}, s="abc")  # noqa
    assert bar.d == {}
    bar.d = {"x": 1}

    assert bar.i == 5
    assert bar.x == "xyz"
    assert bar.d["x"] == 1
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)
    assert Serializer(bar).serialize() == {
        "A": [1, 2, 3],
        "D": {"x": 1},
        "I": 5,
        "S": "abc",
        "X": "xyz",
    }

    Bar._serialization_mapper.append({"I": "number"})
    aggregated_mapper_by_class.clear()
    assert Serializer(bar).serialize() == {
        "A": [1, 2, 3],
        "D": {"x": 1},
        "S": "abc",
        "X": "xyz",
        "number": 5,
    }


def test_direct_assignment_to_allfieldsrequired():
    Bar = AllFieldsRequired[Foo]  # noqa
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    with pytest.raises(TypeError):
        Bar(i=5, a={1, 2})

    bar = Bar(i=5, x="xyz", a={1, 2, 3}, s="abc")
    assert bar.i == 5
    assert bar.s == "abc"
    assert bar.a == {1, 2, 3}
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)


def test_direct_assignment_to_partial_with_class_name():
    Bar = AllFieldsRequired[Foo, "Bar"]  # noqa
    assert Bar.__name__ == "Bar"


def test_partial_immutable():
    class Bar(AllFieldsRequired[Foo], ImmutableStructure):
        x: str

    bar = Bar(i=5, x="xyz", a={1, 2, 3}, s="abc")
    with pytest.raises(ValueError) as excinfo:
        bar.d = {}
    assert "Bar: Structure is immutable" in str(excinfo.value)

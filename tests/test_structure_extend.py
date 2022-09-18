from typing import Optional

import pytest

from typedpy import (
    Deserializer,
    ImmutableStructure,
    Map,
    Structure,
    mappers,
    Serializer,
    Extend,
)
from typedpy.serialization.mappers import aggregated_mapper_by_class


class Blah(Structure):
    i: int
    d: Map[str, int] = dict


class Foo(Blah, ImmutableStructure):
    s: Optional[str]
    a: set

    _serialization_mapper = mappers.TO_LOWERCASE


# noinspection PyUnresolvedReferences
def test_extend_structure():
    class Bar(Extend[Foo]):
        x: str

        _serialization_mapper=Foo.get_aggregated_serialization_mapper()

    assert set(Bar._required) == {"x", "i", "a"}
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(i=5, x="xyz", a={1, 2, 3})  # noqa
    assert bar.d == {}
    assert bar.i == 5
    assert bar.s is None
    bar.d["x"] = 1
    assert bar.d["x"] == 1
    assert set(Bar.get_all_fields_by_name().keys()) == {"x", "i", "a", "s", "d"}
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)
    assert Serializer(bar).serialize() == {
        "A": [1, 2, 3],
        "D": {"x": 1},
        "I": 5,
        "X": "xyz",
    }

    Bar._serialization_mapper.append({"I": "number"})
    aggregated_mapper_by_class.clear()

    assert Serializer(bar).serialize() == {
        "A": [1, 2, 3],
        "D": {"x": 1},
        "X": "xyz",
        "number": 5,
    }


def test_direct_assignment_to_extend():
    Bar = Extend[Foo]
    with pytest.raises(TypeError) as excinfo:
        Bar(i=5, s="xyz")
    assert "ExtendFoo: missing a required argument: 'a'" in str(excinfo.value)

    bar = Bar(i=5, a={1, 2})
    assert bar.s is None
    assert bar.a == {2, 1}
    with pytest.raises(TypeError) as excinfo:
        bar.d = {"x": "y"}
    assert "d_value: Expected <class 'int'>; Got 'y'" in str(excinfo.value)


def test_direct_assignment_to_extend_with_name():
    Bar = Extend[Foo, "Bar"]  # noqa
    with pytest.raises(TypeError) as excinfo:
        Bar(i=5, s="xyz")
    assert "Bar: missing a required argument: 'a'" in str(excinfo.value)
    assert str(Bar).startswith("<Structure: Bar.")


def test_extend_and_immutable():
    class Bar(Extend[Foo], ImmutableStructure):
        x: str

    bar = Bar(i=5, x="xyz", a={"abc", 1, (4, 5, 6)}, d={"x": 1})
    with pytest.raises(ValueError) as excinfo:
        bar.d["x"] = 2  # noqa
    assert "d: Field is immutable" in str(excinfo.value)


def test_extend_serialization_mappers_are_consistent1():
    class Foo(Structure):
        x: str

        _serialization_mapper = mappers.TO_LOWERCASE

    class Bar(Extend[Foo], Structure):
        y: str

    assert Bar.get_aggregated_serialization_mapper() == []
    assert Bar.get_aggregated_deserialization_mapper() == []


def test_extend_serialization_mappers_are_consistent2():
    class Foo(Structure):
        x: str

    class Bar(Extend[Foo], Structure):
        y: str

        _serialization_mapper = mappers.TO_LOWERCASE

    assert Bar._serialization_mapper == mappers.TO_LOWERCASE
    assert not hasattr(Bar, "_deserialization_mapper")
    assert Deserializer(Bar).deserialize({"X": "a", "Y": "b"}) == Bar(x="a", y="b")

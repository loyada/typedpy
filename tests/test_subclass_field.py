import pytest
from typedpy import Map, Structure
from typedpy.subclass import SubClass


class Foo(Structure):
    pass


class Bar(Foo):
    pass


class Baz(Structure):
    pass


def test_correct_usage():
    class Container1(Structure):
        data: Map[SubClass(clazz=Foo), str]

        _additionalProperties = False

    container = Container1(data={Bar: "bar"})
    assert container.data[Bar] == "bar"
    assert Bar in container
    assert Foo not in container


def test_correct_usage_variation():
    class Container1(Structure):
        data: Map[SubClass[Foo], str]

        _additionalProperties = False

    container = Container1(data={Bar: "bar"})
    assert container.data[Bar] == "bar"
    assert Bar in container
    assert Foo not in container


def test_invalid_definition():
    with pytest.raises(TypeError) as excinfo:
        SubClass(clazz=int())

    assert "SubClass must accept a class type as argument" in str(excinfo.value)


def test_invalid_type():
    class Container1(Structure):
        data: Map[SubClass[Foo], str]

    with pytest.raises(TypeError) as excinfo:
        Container1(data={Baz: "baz"})

    assert (
        "data_key: Expected a subclass of Foo; Got <Structure: Baz. Properties: >"
        in str(excinfo.value)
    )

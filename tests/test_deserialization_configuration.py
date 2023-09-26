import pytest

from typedpy import Deserializer, ImmutableStructure, mappers


def test_configuration_automatic_conversion():
    class Foo(ImmutableStructure):
        a: int
        arr: list[int]
        s: str

        _serialization_mapper = [mappers.CONFIGURATION, mappers.TO_LOWERCASE ]

    deserialized = Deserializer(Foo).deserialize({"A": "123", "ARR": [1, 2], "S": "xxx"})
    assert deserialized == Foo(a=123, arr=[1,2], s="xxx")

def test_configuration_automatic_conversion_deserialization_mapper():
    class Foo(ImmutableStructure):
        a: int
        arr: list[int]
        s: str

        _deserialization_mapper = [mappers.CONFIGURATION, mappers.TO_LOWERCASE ]

    deserialized = Deserializer(Foo).deserialize({"A": "123", "ARR": [1, 2], "S": "xxx"})
    assert deserialized == Foo(a=123, arr=[1,2], s="xxx")


def test_configuration_automatic_conversion_err_missing_mapper():
    class Foo(ImmutableStructure):
        a: int
        arr: list[int]
        s: str

        _serialization_mapper = [ mappers.TO_LOWERCASE ]

    with pytest.raises(TypeError):
        Deserializer(Foo).deserialize({"A": "123", "ARR": [1, 2], "S": "xxx"})


def test_configuration_automatic_conversion_err_bad_val():
    class Foo(ImmutableStructure):
        a: int
        arr: list[int]
        s: str

        _deserialization_mapper = [mappers.CONFIGURATION, mappers.TO_LOWERCASE ]

    with pytest.raises(TypeError):
        Deserializer(Foo).deserialize({"A": "12a3", "ARR": [1, 2], "S": "xxx"})


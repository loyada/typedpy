import sys
from pytest import mark, raises

from typedpy import Deserializer, ImmutableStructure, mappers


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_configuration_automatic_conversion():
    class Foo(ImmutableStructure):
        a: int
        arr: list[int]
        s: str

        _serialization_mapper = [mappers.CONFIGURATION, mappers.TO_LOWERCASE ]

    deserialized = Deserializer(Foo).deserialize({"A": "123", "ARR": [1, 2], "S": "xxx"})
    assert deserialized == Foo(a=123, arr=[1,2], s="xxx")

@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_configuration_automatic_conversion_deserialization_mapper():
    class Foo(ImmutableStructure):
        a: int
        arr: list[int]
        s: str

        _deserialization_mapper = [mappers.CONFIGURATION, mappers.TO_LOWERCASE ]

    deserialized = Deserializer(Foo).deserialize({"A": "123", "ARR": [1, 2], "S": "xxx"})
    assert deserialized == Foo(a=123, arr=[1,2], s="xxx")


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_configuration_automatic_conversion_err_missing_mapper():
    class Foo(ImmutableStructure):
        a: int
        arr: list[int]
        s: str

        _serialization_mapper = [ mappers.TO_LOWERCASE ]

    with raises(TypeError):
        Deserializer(Foo).deserialize({"A": "123", "ARR": [1, 2], "S": "xxx"})


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_configuration_automatic_conversion_err_bad_val():
    class Foo(ImmutableStructure):
        a: int
        arr: list[int]
        s: str

        _deserialization_mapper = [mappers.CONFIGURATION, mappers.TO_LOWERCASE ]

    with raises(TypeError):
        Deserializer(Foo).deserialize({"A": "12a3", "ARR": [1, 2], "S": "xxx"})


import pytest

from typedpy import Array, Deserializer, FunctionCall, Serializer, Structure, mappers
from typedpy.mappers import aggregate_deserialization_mappers, aggregate_serialization_mappers


def test_aggregated_simple_inheritance():
    class Foo(Structure):
        i: int
        _serialization_mapper = {"i": "j"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = mappers.TO_LOWERCASE

    mappers_calculated = Bar.get_aggregated_serialization_mapper()
    assert mappers_calculated == [{"i": "j"}, mappers.TO_LOWERCASE]
    assert Deserializer(Bar).deserialize({"J": 5, "A": [1, 2, 3]}, keep_undefined=False) == Bar(i=5, a=[1, 2, 3])


def test_chain_map_and_lowercase():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": "b"}, mappers.TO_LOWERCASE]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"a": "B", "s": "S"}
    deserialized = Deserializer(Foo).deserialize({"B": 5, "S": "abc"})
    assert deserialized == Foo(a=5, s="abc")


def test_chain_map_and_lowercase_with_nested():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": "b.c"}, mappers.TO_LOWERCASE]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"a": "B.C", "s": "S"}
    deserialized = Deserializer(Foo).deserialize({"B": {"C": 5}, "S": "abc"})
    assert deserialized == Foo(a=5, s="abc")


def test_chain_map_and_camelcase():
    class Foo(Structure):
        a: int
        ssss_ttt: str

        _serialization_mapper = [{"a": "bb_cc"}, mappers.TO_CAMELCASE, {"ssssTtt": "x"}]


    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"a": "bbCc", "ssss_ttt": "x"}
    deserialized = Deserializer(Foo).deserialize({"bbCc": 5, "x": "abc"})
    assert deserialized == Foo(a=5, ssss_ttt="abc")


def test_aggregated_with_function():
    class Foo(Structure):
        xyz: Array
        i: int
        _serialization_mapper = {"i": "j"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = mappers.TO_LOWERCASE

    class Blah(Bar):
        s: str
        foo: Foo
        _serialization_mapper = {}
        _deserialization_mapper = {"S": FunctionCall(func=lambda x: x * 2)}

    aggregated = aggregate_deserialization_mappers(Blah)
    assert aggregated == {
        "xyz": "XYZ",
        "i": "J",
        "a": "A",
        "s": FunctionCall(func=Blah._deserialization_mapper["S"].func, args=["S"]),
        "foo": "FOO",
        "FOO._mapper": {
            "xyz": "XYZ",
            "i": "J"
        }
    }

    original = {
        "S": "abc",
        "FOO": {
            "XYZ": [1, 2],
            "J": 5
        },
        "A": [7, 6, 5, 4],
        "XYZ": [1, 4],
        "J": 9
    }
    deserialized = Deserializer(Blah).deserialize(original, keep_undefined=False)
    assert deserialized == Blah(
        s="abcabc",
        foo=Foo(i=5, xyz=[1, 2]),
        xyz=[1, 4],
        i=9,
        a=[7, 6, 5, 4]
    )
    serialized = Serializer(deserialized).serialize()
    assert serialized == {**original, "S": "abcabc"}


def test_aggregated_with_function_unsupported():
    class Foo(Structure):
        xyz: Array
        i: int
        _serialization_mapper = {"i": "j"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = mappers.TO_LOWERCASE

    class Blah(Bar):
        s: str
        foo: Foo
        _serialization_mapper = {"S": FunctionCall(func=lambda x: x * 2)}

    blah = Blah(
        s="abcabc",
        foo=Foo(i=5, xyz=[1, 2]),
        xyz=[1, 4],
        i=9,
        a=[7, 6, 5, 4]
    )
    with pytest.raises(NotImplementedError) as excinfo:
        Serializer(blah).serialize()
    assert "Combining functions and other mapping in a serialization mapper is unsupported" in str(excinfo.value)



def test_chained_mappers():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": "b"}, mappers.TO_LOWERCASE]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {
        "a": "B",
        "s": "S"
    }
    original = {"B": 5, "S": "xyz"}
    deserialized = Deserializer(Foo).deserialize(original, keep_undefined=False)
    assert deserialized == Foo(a=5, s="xyz")
    serialized = Serializer(deserialized).serialize()
    assert serialized == original

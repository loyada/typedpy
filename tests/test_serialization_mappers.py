import pytest

from typedpy import (
    Array,
    Deserializer,
    FunctionCall,
    Serializer,
    String,
    Structure,
    mappers,
)
from typedpy.mappers import (
    DoNotSerialize,
    aggregate_deserialization_mappers,
    aggregate_serialization_mappers,
)


def test_aggregated_simple_inheritance():
    class Foo(Structure):
        i: int
        _serialization_mapper = {"i": "j"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = mappers.TO_LOWERCASE

    mappers_calculated = Bar.get_aggregated_serialization_mapper()
    assert mappers_calculated == [{"i": "j"}, mappers.TO_LOWERCASE]
    assert Deserializer(Bar).deserialize(
        {"J": 5, "A": [1, 2, 3]}, keep_undefined=False
    ) == Bar(i=5, a=[1, 2, 3])


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
        "FOO._mapper": {"xyz": "XYZ", "i": "J"},
    }

    original = {
        "S": "abc",
        "FOO": {"XYZ": [1, 2], "J": 5},
        "A": [7, 6, 5, 4],
        "XYZ": [1, 4],
        "J": 9,
    }
    deserialized = Deserializer(Blah).deserialize(original, keep_undefined=False)
    assert deserialized == Blah(
        s="abcabc", foo=Foo(i=5, xyz=[1, 2]), xyz=[1, 4], i=9, a=[7, 6, 5, 4]
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

    blah = Blah(s="abcabc", foo=Foo(i=5, xyz=[1, 2]), xyz=[1, 4], i=9, a=[7, 6, 5, 4])
    with pytest.raises(NotImplementedError) as excinfo:
        Serializer(blah).serialize()
    assert (
        "Combining functions and other mapping in a serialization mapper is unsupported"
        in str(excinfo.value)
    )


def test_chained_mappers():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": "b"}, mappers.TO_LOWERCASE]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"a": "B", "s": "S"}
    original = {"B": 5, "S": "xyz"}
    deserialized = Deserializer(Foo).deserialize(original, keep_undefined=False)
    assert deserialized == Foo(a=5, s="xyz")
    serialized = Serializer(deserialized).serialize()
    assert serialized == original


def test_mapper_with_opt():
    class Foo(Structure):
        first = String
        second = String
        opt = String
        _optional = ["opt"]
        _serialization_mapper = mappers.TO_LOWERCASE

    foo: Foo = Deserializer(Foo).deserialize(
        {"FIRST": "ff", "SECOND": "ss", "OPT": "oo"}
    )
    foo2: Foo = Deserializer(Foo).deserialize({"FIRST": "ff", "SECOND": "ss"})
    foo2.opt = foo.opt
    assert foo == foo2


def test_dont_serialize():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": DoNotSerialize}]

    assert Serializer(Foo(a=5, s="xyz")).serialize() == {"s": "xyz"}


def test_dont_serialize_chained():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": DoNotSerialize}, mappers.TO_LOWERCASE]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"s": "S", "a": DoNotSerialize}
    assert Serializer(Foo(a=5, s="xyz")).serialize() == {"S": "xyz"}


def test_dont_serialize_inheritance_chained():
    class Foo(Structure):
        i: int
        s: str
        _serialization_mapper = {"i": "j", "s": "name"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = [{"j": DoNotSerialize}, mappers.TO_LOWERCASE]
        _deserialization_mapper = [mappers.TO_LOWERCASE]

    aggregated = aggregate_serialization_mappers(Bar)
    assert aggregated == {"s": "NAME", "a": "A", "i": DoNotSerialize}
    deserialized = Deserializer(Bar).deserialize(
        {"J": 5, "A": [1, 2, 3], "NAME": "jon"}, keep_undefined=False
    )
    assert deserialized == Bar(i=5, a=[1, 2, 3], s="jon")
    assert Serializer(deserialized).serialize() == {"NAME": "jon", "A": [1, 2, 3]}

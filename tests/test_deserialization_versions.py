import sys

from pytest import mark
from typedpy import Array, Deserializer, FunctionCall, ImmutableStructure, Integer, Map, PositiveInt, String, Structure, \
    Versioned, convert_dict
from typedpy.mappers import Constant, Deleted


class Bar(ImmutableStructure):
    a: Array[Integer]
    s: String


class Foo(Versioned, ImmutableStructure):
    bar: Bar
    i: Integer
    j: Integer
    m: Map[String, String]
    nested: str

    _versions_mapping = [
        {
            "j": Constant(100),
            "old_bar._mapper": {
                "a": FunctionCall(func=lambda x: [i * 2 for i in x], args=["a"]),
            },
            "old_m": Constant({"abc": "xyz"})
        },

        {
            "old_bar._mapper": {
                "s": "sss",
                "sss": Deleted
            },
            "bar": "old_bar",
            "m": "old_m",
            "old_m": Deleted,
            "old_bar": Deleted,
        },

        {
            "i": FunctionCall(func=lambda x: x * 100, args=["i"]),
            "nested": "bar.s"
        }

    ]


in_version_1 = {
    "version": 1,
    "old_bar": {
        "a": [5, 8, 2],
        "sss": "john",
    },
    "i": 2,
    "old_m": {"a": "aa", "b": "bb"}
}

in_version_2 = {
    "version": 2,
    "old_bar": {
        "a": [10, 16, 4],
        "sss": "john",
    },
    "i": 2,
    "j": 150,
    "old_m": {"abc": "xyzxyzxyzyxyzxyzxyzxz", "b": "bb"}
}


def test_version_conversion_deserializer():
    assert Deserializer(Foo).deserialize(in_version_1) == Foo(
        bar=Bar(a=[10, 16, 4], s="john"),
        m={"abc": "xyz"},
        i=200,
        j=100,
        nested="john",
        version=4
    )

    assert Deserializer(Foo).deserialize(in_version_2) == Foo(
        bar=Bar(a=[10, 16, 4], s="john"),
        m={"abc": "xyzxyzxyzyxyzxyzxyzxz", "b": "bb"},
        i=200,
        j=150,
        nested="john",
        version=4
    )


def test_version_conversion_without_deserializer():
    expected_in_latest_version = {
        "version": 4,
        "bar": {
            "a": [10, 16, 4],
            "s": "john",
        },
        "i": 200,
        "j": 100,
        "nested": "john",
        "m": {"abc": "xyz"},
    }
    assert convert_dict(in_version_1, Foo._versions_mapping) == expected_in_latest_version
    assert convert_dict(expected_in_latest_version, Foo._versions_mapping) == expected_in_latest_version


def test_deserialize_versioned_mapper_defect():
    class FooBar(ImmutableStructure):
        data = String

    class Foo(ImmutableStructure):
        data = String
        bar = FooBar

    class VersionedFoo(Versioned):
        foo = Foo
        _versions_mapping = [
            {
                "foo._mapper": {
                    "data": "string_data",
                    "string_data": Deleted,
                    "bar": "foobar",
                    "foobar": Deleted,
                    "foobar._mapper": {
                        "data": "string_data",
                        "string_data": Deleted,

                    }
                }
            }
        ]

    v1 = {
        "version": 1,
        "foo": {
            "string_data": "Foo",
            "foobar": {
                "string_data": "FooBar"
            }
        }
    }

    v2 = {
        "version": 2,
        "foo": {
            "data": "Foo",
            "bar": {
                "data": "FooBar"
            }
        }
    }
    wrapped_v2: VersionedFoo = Deserializer(VersionedFoo).deserialize(v2)
    wrapped_v1: VersionedFoo = Deserializer(VersionedFoo).deserialize(v1)

    assert wrapped_v1.foo == wrapped_v2.foo


def test_versioned_populates_version_automatically():
    assert Foo(
        bar=Bar(a=[10, 16, 6], s="john"),
        m={"abc": "xcxcxcxcxcxc", "b": "bb"},
        i=200,
        nested="john",
        j=150
    ).version == 4


def test_version_populated_automatically_when_no_mapping():
    class Example(Versioned):
        i: int

    assert Example(i=5).version == 1


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_mapping_list_of_objects():
    class Example(Versioned):
        i: list[Bar]

        _versions_mapping = [
            {
                "i._mapper": {
                    "s": "sss",
                    "sss": Deleted
                }
            }
        ]

    serialized = {
        "i": [
            {
                "sss": "xyz",
                "a": [1, 2, 3]
            }
        ]
    }

    assert Deserializer(Example).deserialize(serialized) == Example(
        i=[
            Bar(s="xyz", a=[1, 2, 3])
        ]
    )


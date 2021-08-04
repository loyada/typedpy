import copy

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
                "i": FunctionCall(func=lambda x: x * 100, args=["i"])
            }

    ]


in_version_1 = {
    "version": 1,
    "old_bar": {
        "a": [5,8,2],
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


def test_version_conversion():
    assert Deserializer(Foo).deserialize(in_version_1) == Foo(
        bar=Bar(a=[10, 16, 4], s="john"),
        m={"abc": "xyz"},
        i=200,
        j=100,
        version=4
    )

    assert Deserializer(Foo).deserialize(in_version_2) == Foo(
        bar=Bar(a=[10, 16, 4], s="john"),
        m={"abc": "xyzxyzxyzyxyzxyzxyzxz", "b": "bb"},
        i=200,
        j=150,
        version=4
    )


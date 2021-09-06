import typing
from typing import List

from pytest import raises
from typedpy import Array, Deserializer, Integer, SerializableField, Serializer, String, Structure


def test_list_of_string_var_1():
    class Foo(Structure):
        a: list[String]
        i: int

    deserializer = Deserializer(Foo)
    foo = Foo(i=5, a=["abc", "def"])
    assert foo.a[0] == "abc"

    serialized = {"a": ["abc", "def"], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo

    assert Serializer(deserialized).serialize() == serialized


def test_list_of_string_var_2():
    class Foo(Structure):
        a: list[set[String]]
        i: int

    deserializer = Deserializer(Foo)
    foo = Foo(i=5, a=[{"abc", "def"}])
    assert "abc" in foo.a[0]

    serialized = {"a": [{"abc", "def"}], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo

    result = Serializer(deserialized).serialize()
    for s in deserialized.a[0]:
        assert s in result["a"][0]


def test_list_of_string_var_3():
    class Foo(Structure):
        a: List[String]
        i: int

    deserializer = Deserializer(Foo)
    foo = Foo(i=5, a=["abc", "def"])
    assert foo.a[0] == "abc"

    serialized = {"a": ["abc", "def"], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo

    assert Serializer(deserialized).serialize() == serialized


def test_list_of_string_var_4():
    class Foo(Structure):
        a: list[typing.Set[String]]
        i: int

    deserializer = Deserializer(Foo)
    foo = Foo(i=5, a=[{"abc", "def"}])
    assert "abc" in foo.a[0]
    serialized = {"a": [{"abc", "def"}], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo
    result = Serializer(deserialized).serialize()
    for s in deserialized.a[0]:
        assert s in result["a"][0]
    assert result["i"] == 5


def test_list_of_string_var_5():
    class Foo(Structure):
        a: typing.List[typing.Set[String]]
        i: int

    deserializer = Deserializer(Foo)
    foo = Foo(i=5, a=[{"abc", "def"}])
    assert "abc" in foo.a[0]
    serialized = {"a": [{"abc", "def"}], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo
    result = Serializer(deserialized).serialize()
    for s in deserialized.a[0]:
        assert s in result["a"][0]
    assert result["i"] == 5


def test_list_of_string_var_6():
    class Foo(Structure):
        a: typing.List[typing.Set[String]]
        i: int

    deserializer = Deserializer(Foo)
    foo = Foo(i=5, a=[{"abc", "def"}])
    assert "abc" in foo.a[0]
    serialized = {"a": [{"abc", "def"}], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo
    result = Serializer(deserialized).serialize()
    for s in deserialized.a[0]:
        assert s in result["a"][0]
    assert result["i"] == 5


def test_array_of_str():
    class Foo(Structure):
        a: Array[str]
        i: int

    deserializer = Deserializer(Foo)
    foo = Foo(i=5, a=["abc", "def"])
    assert "abc" in foo.a[0]
    serialized = {"a": ["abc", "def"], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo
    result = Serializer(deserialized).serialize()
    assert result == serialized

    with raises(ValueError) as excinfo:
        deserializer.deserialize({"a": ["abc", 123], "i": 5})
    assert "a_1: Got 123; Expected a string" in str(excinfo.value)


def test_array_of_dict_1():
    class Foo(Structure):
        a: Array[dict[str, Integer]]
        i: int

    deserializer = Deserializer(Foo)
    foo = Foo(i=5, a=[{"abc": 1}, {"abc": 2}])
    assert foo.a[0] == {"abc": 1}
    serialized = {"a": [{"abc": 1}, {"abc": 2}], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo
    result = Serializer(deserialized).serialize()
    assert result == serialized

    with raises(ValueError) as excinfo:
        deserializer.deserialize({"a": [{"abc": "xxx"}], "i": 5})
    assert "a_0: a_1_value: Expected <class 'int'>; Got 'xxx'" in str(excinfo.value)


def test_array_of_dict_2():
    class Foo(Structure):
        a: Array[dict[String, int]]
        i: int

    deserializer = Deserializer(Foo)
    foo = Foo(i=5, a=[{"abc": 1}, {"abc": 2}])
    assert foo.a[0] == {"abc": 1}
    serialized = {"a": [{"abc": 1}, {"abc": 2}], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo
    result = Serializer(deserialized).serialize()
    assert result == serialized

    with raises(ValueError) as excinfo:
        deserializer.deserialize({"a": [{"abc": "xxx"}], "i": 5})
    assert "a_0: a_1_value: Expected <class 'int'>; Got 'xxx'" in str(excinfo.value)

    with raises(ValueError) as excinfo:
        deserializer.deserialize({"a": [{1: 123}], "i": 5})
    assert "a_0: a_1_key: Got 1; Expected a string" in str(excinfo.value)


def test_array_of_dict_3():
    class Foo(Structure):
        a: Array[dict[String(minLength=5), int]]
        i: int

    with raises(ValueError) as excinfo:
        Foo(i=5, a=[{"abc": 1}, {"abc": 2}])
    assert "a_0_key: Got 'abc'; Expected a minimum length of 5" in str(excinfo.value)

    deserializer = Deserializer(Foo)

    foo = Foo(i=5, a=[{"abcde": 1}, {"abc123": 2}])
    assert foo.a[0] == {"abcde": 1}
    serialized = {"a": [{"abcde": 1}, {"abc123": 2}], "i": 5}
    deserialized = deserializer.deserialize(serialized)
    assert deserialized == foo
    result = Serializer(deserialized).serialize()
    assert result == serialized


def test_list_of_string_var_2_invalid():
    class Foo(Structure):
        a: list[set[String]]
        i: int

    deserializer = Deserializer(Foo)
    with raises(TypeError) as excinfo:
        Foo(i=5, a=[{"abc", "def"}, 123])
    assert "a_1: Got 123; Expected <class 'set'>" in str(excinfo.value)

    serialized = {"a": [{"abc", "def"}, 123], "i": 5}
    with raises(ValueError) as excinfo:
        deserializer.deserialize(serialized)
    assert "a_1: Got 123; Expected a list, set, or tuple" in str(excinfo.value)


def test_optional_simple():
    class Foo(Structure):
        a: typing.Optional[set[String]]
        i: int

    foo = Foo(i=5)
    foo.a = {"abc"}
    assert foo.a == {"abc"}
    assert Foo(i=5, a={"abc"}) == foo
    assert Deserializer(Foo).deserialize({"i": 5}) == Foo(i=5)
    assert Deserializer(Foo).deserialize({"i": 5, "a": ["abc"]}) == foo
    assert Serializer(foo).serialize() == {"i": 5, "a": ["abc"]}


def test_default_factory_invalid_default():
    with raises(TypeError) as excinfo:
        class Foo(Structure):
            a: list[str] = lambda: [1, 2, 3]
            i: int
    assert "a: Invalid default value: [1, 2, 3]; Reason: value_0: Got 1; Expected a string" in str(excinfo.value)


def test_default_factory_valid():
    class Foo(Structure):
        a: list[str] = lambda: ["abc", "def"]
        i: int

    foo1 = Foo(i=1)
    foo2 = Foo(i=2)
    foo1.a.append("xxx")
    assert foo1.a == ["abc", "def", "xxx"]
    assert foo2.a == ["abc", "def"]


def test_dict_to_map():
    class TestSerializable(SerializableField):
        def serialize(self, value):
            return value.rstrip()

        def deserialize(self, value):
            return value + "                    "

    class Foo(Structure):
        a: dict[str, TestSerializable]
        i: int

    foo = Deserializer(Foo).deserialize({"i": 5, "a": {"abc": "xxx"}})
    assert foo.a["abc"] == "xxx" + "                    "

    assert Serializer(foo).serialize() == {"i": 5, "a": {"abc": "xxx"}}


def test_dict_to_map_invalid():
    class Foo(Structure):
        a: dict[str, Array[String]]
        i: int

    with raises(ValueError) as excinfo:
        Deserializer(Foo).deserialize({"i": 5, "a": {"abc": ["xxx", "yyy", 2]}})
    assert "a_2: Expected a string" in str(excinfo.value)

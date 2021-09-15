from pytest import raises

from typedpy import AllOf, Deserializer, Integer, NotField, Positive, Serializer, String, Structure


def test_simple_not():
    class Foo(Structure):
        i: NotField[String, Positive]

    assert Foo(i=-5).i == -5
    with raises(ValueError) as excinfo:
        Foo(i="xyz")
    assert "i: Got 'xyz'; Expected not to match any field definition" in str(excinfo.value)
    with raises(ValueError) as excinfo:
        Foo(i=5)
    assert "i: Got 5; Expected not to match any field definition" in str(excinfo.value)


def test_negative_int():
    class Foo(Structure):
        i: AllOf[NotField[Positive], Integer]

    assert Foo(i=-5).i == -5
    with raises(ValueError) as excinfo:
        Foo(i=5)
    assert "i: Got 5; Expected not to match any field definition" in str(excinfo.value)


def test_allof_with_not():
    class Foo(Structure):
        i: AllOf[NotField[Positive], Integer]

    with raises(TypeError) as excinfo:
        Foo(i=-0.5)
    assert "i: Expected <class 'int'>; Got -0.5" in str(excinfo.value)


def test_negative_int_serialization():
    class Foo(Structure):
        i: AllOf[NotField[Positive], Integer]

    deserialized = Deserializer(Foo).deserialize({"i": -5})
    assert deserialized.i == -5
    assert Serializer(deserialized).serialize() == {"i": -5}
    with raises(ValueError) as excinfo:
        Deserializer(Foo).deserialize({"i": 1})
    assert "i: Got 1; Expected not to match any field definition" in str(excinfo.value)

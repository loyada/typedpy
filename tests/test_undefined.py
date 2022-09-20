from typedpy import Deserializer, Serializer, Structure, Undefined


class Foo(Structure):
    a: int
    b: int
    c: int
    _required = []
    _ignore_none = True
    _enable_undefined_value = True


def test_undefined():
    assert Foo(a=4, c=None).b is Undefined
    print(Foo(a=4, c=None))
    foo = Deserializer(Foo).deserialize({"a": 1, "b": None})
    assert foo == Foo(a=1, b=None)
    assert foo != Foo(a=1)
    assert foo.shallow_clone_with_overrides(a=2) == Foo(a=2, b=None)
    assert foo != Foo(a=1, b=None, c=None)
    assert foo.c is Undefined
    assert foo.b is not Undefined


def test_undefined_serialization():
    foo = Deserializer(Foo).deserialize({"a": 1, "b": None})
    assert Serializer(foo).serialize() == {"a": 1, "b": None}
    assert Serializer(Foo(a=None)).serialize() == {"a": None}
    assert Serializer(Foo()).serialize() == {}

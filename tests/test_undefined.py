from typedpy import Deserializer, Serializer, Structure, Undefined


class Foo(Structure):
    a: int
    b: int
    c: int
    d: int = 5
    _required = []
    _ignore_none = True
    _enable_undefined_value = True


def test_undefined():
    assert Foo(a=4, c=None).b is Undefined
    assert (
        str(Foo(a=4, c=None)) == "<Instance of Foo. Properties: a = 4, d = 5, c = None>"
    )
    foo: Foo = Deserializer(Foo).deserialize({"a": 1, "b": None})
    assert foo == Foo(a=1, b=None)
    assert not foo.c
    assert foo.to_other_class(dict) == {"a": 1, "b": None, "d": 5}
    assert foo.to_other_class(dict, c=Undefined) == {"a": 1, "b": None, "d": 5}
    assert foo != Foo(a=1)
    assert foo.shallow_clone_with_overrides(a=2) == Foo(a=2, b=None)
    assert foo != Foo(a=1, b=None, c=None)
    assert foo.c is Undefined
    assert foo.b is not Undefined
    assert foo.shallow_clone_with_overrides(d=999) == Foo(a=1, b=None, d=999)


class Bar(Structure):
    a: int
    b: int
    c: int
    _required = []
    _ignore_none = True
    _enable_undefined_value = True


def test_undefined_serialization():
    foo = Deserializer(Foo).deserialize({"a": 1, "b": None})
    assert Serializer(foo).serialize() == {"a": 1, "b": None, "d": 5}
    assert Serializer(Foo(a=None)).serialize() == {"a": None, "d": 5}
    assert Serializer(Foo()).serialize() == {"d": 5}
    assert Serializer(Bar()).serialize() == {}

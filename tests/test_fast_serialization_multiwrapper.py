from typing import Optional, Union

from pytest import raises

from typedpy import FastSerializable, ImmutableStructure, OneOf, Structure, create_serializer, serialize
from typedpy.structures.structures import created_fast_serializer, failed_to_create_fast_serializer


class Foo1(Structure, FastSerializable):
    foo1: str

class Foo2(Structure, FastSerializable):
    foo2: str



create_serializer(Foo1)
create_serializer(Foo2)


def test_fastserializable_AnyOf_unsupported():
    class Bar(Structure, FastSerializable):
        foo: Union[Foo1, Foo2]

    with raises(TypeError) as excinfo:
        create_serializer(Bar)
    assert "AnyOf(i.e. Union) is not FastSerializable when it can be multiple types" in str(excinfo.value)


def test_fastserializable_OneOf_unsupported():
    class Bar(Structure, FastSerializable):
        foo: OneOf[Foo1, Foo2]

    with raises(TypeError) as excinfo:
        create_serializer(Bar)
    assert "<OneOf [<ClassReference: Foo1>, <ClassReference: Foo2>]> Field is not FastSerializable" in str(excinfo.value)


def test_fastserializable_optional():
    class Bar(Structure, FastSerializable):
        foo: Optional[Foo2]

    class BarWrapper(ImmutableStructure, FastSerializable):
        bar: Bar


    foo = Foo2(foo2="foo2")
    bar = Bar(foo=foo)
    barwrapper = BarWrapper.from_other_class({}, bar = bar)
    serialized = barwrapper.serialize()
    assert serialized == {'bar': {'foo': {"foo2": "foo2"}}}

    barwrapper = BarWrapper.from_other_class({}, bar=Bar())
    serialized = barwrapper.serialize()
    assert serialized == {'bar': {}}

def test_fastserializable_optional_1():
    class Bar(Structure, FastSerializable):
        foo: Optional[Foo2]

    class BarWrapper(ImmutableStructure, FastSerializable):
        bar: Bar


    foo = Foo2(foo2="foo2")
    bar = Bar(foo=foo)
    barwrapper = BarWrapper.from_other_class({}, bar = bar)
    serialized = serialize(barwrapper)
    assert serialized == {'bar': {'foo': {"foo2": "foo2"}}}

    barwrapper = BarWrapper.from_other_class({}, bar=Bar())
    serialized = serialize(barwrapper)
    assert serialized == {'bar': {}}
    assert getattr(BarWrapper, created_fast_serializer)
    assert not getattr(BarWrapper, failed_to_create_fast_serializer, False)
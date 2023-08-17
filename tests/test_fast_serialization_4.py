import enum
import enum
import sys
from typing import Optional

from typedpy.serialization.fast_serialization import (
    FastSerializable,
    create_serializer,
)
from typedpy.structures.structures import created_fast_serializer, failed_to_create_fast_serializer

python_ver_atleast_than_37 = sys.version_info[0:2] > (3, 6)
if python_ver_atleast_than_37:
    pass

from pytest import raises

from typedpy import (
    ImmutableStructure,
    NoneField,
    SerializableField,
    Structure,
    Array,
    Number,
    String,
    Integer,
    StructureReference,
    AllOf,
    Enum,
    Float,
    mappers,
    AnyOf,
    Map,
    serialize, Deserializer,
    Serializer,
)


class SimpleStruct(Structure, FastSerializable):
    name = String(pattern="[A-Za-z]+$", maxLength=8)


class Point2:
    def __init__(self, x, y):
        self._x = x
        self._y = y


class Example(Structure, FastSerializable):
    i = Integer(maximum=10)
    s = String(maxLength=5)
    array = Array[Integer(multiplesOf=5), Number]
    embedded = StructureReference(a1=Integer(), a2=Float())
    simple_struct = SimpleStruct
    all = AllOf[Number, Integer]
    enum = Enum(values=[1, 2, 3])
    points = Array[Point2]
    _optional = ["points"]


create_serializer(SimpleStruct)



def test_serialize_mapper_to_lowercase(no_defensive_copy_on_get):
    class Bar(Structure, FastSerializable):
        field1 = String
        field2 = String

        _serialization_mapper = mappers.TO_LOWERCASE

    class Foo(Structure, FastSerializable):
        abc = Integer
        m = Map[String, Bar]

        _serialization_mapper = mappers.TO_LOWERCASE

    foo = Foo(abc=123, m={"my_key": Bar(field1="xxx", field2="yyy")})
    serialized = serialize(foo)
    assert serialized == {
        "ABC": 123,
        "M": {"my_key": {"FIELD1": "xxx", "FIELD2": "yyy"}},
    }
    assert Deserializer(Foo).deserialize(serialized) == foo


def test_serialize_anyof(no_defensive_copy_on_get):
    class TestSerializable(SerializableField):
        def serialize(self, value):
            return value.rstrip()

        def deserialize(self, value):
            return value + "  "

    class Container(ImmutableStructure, FastSerializable):
        field1: String
        field2: AnyOf[NoneField, TestSerializable]


    f = {"field1": "val1", "field2": "val2"}
    f2d = Deserializer(Container).deserialize(f)
    # remove serializer
    setattr(Container, created_fast_serializer, False)
    Container.serialize = FastSerializable.serialize

    f2s = serialize(f2d)
    assert f2s == f

    assert getattr(Container, created_fast_serializer)
    assert not getattr(Container, failed_to_create_fast_serializer, False)


def test_serialize_optional_of_serializablefield(no_defensive_copy_on_get):
    class TestSerializable(SerializableField):
        def serialize(self, value):
            return value.rstrip()

        def deserialize(self, value):
            return value + "  "

    class Container1(ImmutableStructure, FastSerializable):
        field1: String
        field2: Optional[TestSerializable]

    class Container2(ImmutableStructure, FastSerializable):
        field1: String
        field2: TestSerializable

    f = {"field1": "val1", "field2": "val2"}

    f2d = Deserializer(Container2).deserialize(f)
    f2s = serialize(f2d)
    assert f2s == f

    f1d = Deserializer(Container1).deserialize(f)
    f1s = serialize(f1d)
    assert f1s == f


def test_trivial_serializable(no_defensive_copy_on_get):
    class Foo(SerializableField):
        pass

    class Bar(Structure, FastSerializable):
        foo: Foo


    deserialized = Bar(foo=123)
    serialized = {"foo": 123}
    assert Deserializer(Bar).deserialize(serialized) == deserialized
    assert serialize(deserialized) == serialized


def test_serialize_multified_with_any1(no_defensive_copy_on_get):
    class MyPoint22:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Foo(Structure, FastSerializable):
        a: Array[AnyOf[Integer, MyPoint22]]


    foo = Foo(a=[1, MyPoint22(1, 2)])
    with raises(TypeError) as excinfo:
        serialize(foo)
    assert "Object of type MyPoint22 is not JSON serializable" in str(excinfo.value)


def test_optional_field_defect_234(no_defensive_copy_on_get):
    class Number(enum.Enum):
        One = 1
        Two = 2
        Three = 3

    class Foo(Structure, FastSerializable):
        a: Optional[Number]

    class Bar(ImmutableStructure, FastSerializable):
        foo: Foo


    foo = Foo(a=Number.One)
    bar = Bar(foo=foo)
    serialize(bar)



def test_do_not_serialize_none(no_defensive_copy_on_get, allow_none_for_optional):
    class Foo(Structure, FastSerializable):
        a: Optional[Number]
        b: int
        c: str

        _required = []

    assert serialize(Foo(c="xxx", b=None, a=None)) == {"c": "xxx"}


def test_serialize_none(no_defensive_copy_on_get, allow_none_for_optional):
    class Foo(Structure, FastSerializable):
        a: Optional[Number]
        b: int
        c: str

        _required = []

    create_serializer(Foo, serialize_none=True)
    assert serialize(Foo(c="xxx", b=None)) == {"c": "xxx", "a": None, "b": None}


def test_inheritance_fastserializable(no_defensive_copy_on_get, allow_none_for_optional):
    class Base(Structure, FastSerializable):
        i: int

    class Foo(Base, FastSerializable):
        s: str


    Base(i=5)
    serialized = Serializer(Foo(i=5, s="xxx")).serialize()
    assert serialized == {"i": 5, "s": "xxx"}


def test_optional_fastserializable(no_defensive_copy_on_get, allow_none_for_optional):

    class Bar(Structure, FastSerializable):
        i: int


    class Foo(Structure, FastSerializable):
        s: Optional[str]
        s1: Optional[str]
        arr: list[Optional[Bar]]


    serialized = Serializer(Foo(s1=None, s="xxx", arr=[None, Bar(i=5), None])).serialize()
    assert serialized == { "s": "xxx", "arr": [None, {"i": 5}, None]}

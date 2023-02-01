import datetime
import enum
import sys
from decimal import Decimal
from typing import Optional

from typedpy.serialization.fast_serialization import (
    FastSerializable,
    create_serializer,
)

python_ver_atleast_than_37 = sys.version_info[0:2] > (3, 6)
if python_ver_atleast_than_37:
    pass

import pytest
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
    deserialize_structure,
    Enum,
    Float,
    mappers,
    Set,
    AnyOf,
    DateField,
    Anything,
    Map,
    Function,
    PositiveInt,
    DecimalNumber,
    serialize_field,
    FunctionCall,
    Deserializer,
    DateTime,
)


class SimpleStruct(Structure, FastSerializable):
    name = String(pattern="[A-Za-z]+$", maxLength=8)


class Point1:
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
    points = Array[Point1]
    _optional = ["points"]


create_serializer(SimpleStruct)


def test_serialize_created_on_instantiation():
    serialized = {"i": 5, "s": "test"}

    class Foo(Structure, FastSerializable):
        i = Integer(maximum=10)
        s = String(maxLength=5)

    assert not hasattr(Foo, "serialize")
    example = deserialize_structure(Foo, serialized)
    assert example.serialize() == serialized


def test_serialize_created_on_instantiation_only_once():
    class Foo(Structure, FastSerializable):
        i = Integer(maximum=10)
        s = String(maxLength=5)

    Foo(i=1, s="x")
    serialize_method = getattr(Foo, "serialize")
    assert serialize_method
    Foo(i=1, s="x")
    assert getattr(Foo, "serialize") is serialize_method


create_serializer(Example)


@pytest.fixture(name="serialized_example")
def fixture_serialized_source():
    return {
        "i": 5,
        "s": "test",
        "array": [10, 7],
        "embedded": {"a1": 8, "a2": 0.5},
        "simple_struct": {"name": "danny"},
        "all": 5,
        "enum": 3,
    }


@pytest.fixture(name="example")
def fixture_example(serialized_example):
    return deserialize_structure(Example, serialized_example)


def test_successful_deserialization_with_many_types(serialized_example, example):
    result = Example.serialize(example)
    assert {k: v for k, v in result.items() if v is not None} == serialized_example


def test_fast_serialization_with_non_typedpy_wrapper_may_fail(
        serialized_example, example
):
    serialized_example["points"] = [{"x": 1, "y": 2}]
    example = deserialize_structure(Example, serialized_example)
    with raises(TypeError) as excinfo:
        result = Example.serialize(example)
    assert "Object of type Point1 is not JSON serializable" in str(excinfo.value)


def test_some_empty_fields():
    class Foo(Structure, FastSerializable):
        a = Integer
        b = String
        _required = []

    foo = Foo(a=5)
    create_serializer(Foo, serialize_none=True)
    assert Foo.serialize(foo) == {"a": 5, "b": None}


def test_null_fields():
    class Foo(Structure, FastSerializable):
        a = Integer
        b = String
        _required = []

    create_serializer(Foo, serialize_none=True)

    foo = Foo(a=5, c=None)
    assert Foo.serialize(foo) == {"a": 5, "b": None}


def test_serialize_set():
    class Foo(Structure, FastSerializable):
        a = Set()

    create_serializer(Foo)

    foo = Foo(a={1, 2, 3})
    assert Foo.serialize(foo) == {"a": [1, 2, 3]}


def test_string_field_wrapper_compact():
    class Foo(Structure, FastSerializable):
        st = String
        _additionalProperties = False

    create_serializer(Foo, compact=True)

    foo = Foo(st="abcde")
    assert Foo.serialize(foo) == "abcde"


def test_string_field_wrapper_not_compact():
    class Foo(Structure, FastSerializable):
        st = String
        _additionalProperties = False

    create_serializer(Foo)

    foo = Foo(st="abcde")
    assert Foo.serialize(foo) == {"st": "abcde"}


def test_set_field_wrapper_compact2():
    class Foo(Structure, FastSerializable):
        s = Array[AnyOf[String, Number]]
        _additionalProperties = False

    create_serializer(Foo, compact=True)

    foo = Foo(s=["abcde", 234])
    assert Foo.serialize(foo) == ["abcde", 234]


def test_serializable_serialize_and_deserialize():
    from datetime import date

    class Foo(Structure, FastSerializable):
        d = Array[DateField(date_format="%y%m%d")]
        i = Integer

    create_serializer(Foo)

    foo = Foo(d=[date(2019, 12, 4), "191205"], i=3)
    serialized = Foo.serialize(foo)
    assert serialized == {"d": ["191204", "191205"], "i": 3}

    deserialized = deserialize_structure(Foo, serialized)
    assert deserialized == Foo(i=3, d=[date(2019, 12, 4), date(2019, 12, 5)])


def test_serialize_map_without_any_type_definition_may_not_know_how_to_serialize():
    class Bar(Structure, FastSerializable):
        m = Map()
        a = Integer

    create_serializer(Bar)

    embedded = Bar(a=2, m={"x": "xx"})
    original = Bar(a=3, m={"abc": embedded, "bcd": 2})
    serialized = Bar.serialize(original)
    assert serialized["m"]["abc"] == embedded


def test_serializable_serialize_and_deserialize2():
    from datetime import datetime

    class Foo(Structure, FastSerializable):
        d = Array[DateTime]
        i = Integer

    create_serializer(Foo)

    atime = datetime(2020, 1, 30, 5, 35, 35)
    atime_as_string = atime.strftime("%m/%d/%y %H:%M:%S")
    foo = Foo(d=[atime, "01/30/20 05:35:35"], i=3)
    serialized = Foo.serialize(foo)
    assert serialized == {"d": [atime_as_string, "01/30/20 05:35:35"], "i": 3}

    deserialized = deserialize_structure(Foo, serialized)
    assert str(deserialized) == str(
        Foo(i=3, d=[atime, datetime(2020, 1, 30, 5, 35, 35)])
    )


def test_serialize_ignore_non_fields_values():
    from datetime import datetime

    class Foo(Structure, FastSerializable):
        d = DateTime
        i = Integer

    create_serializer(Foo)

    atime = datetime(2020, 1, 30, 5, 35, 35)
    foo = Foo(d=atime, i=3, x=atime)
    assert Foo.serialize(foo) == {"d": "01/30/20 05:35:35", "i": 3}


def test_serialize_map():
    class Foo(Structure, FastSerializable):
        m1 = Map[String, Anything]
        m2 = Map
        i = Integer

    create_serializer(Foo)

    foo = Foo(m1={"a": [1, 2, 3], "b": 1}, m2={1: 2, "x": "b"}, i=5)
    serialized = Foo.serialize(foo)
    assert serialized["m1"] == {"a": [1, 2, 3], "b": 1}


def test_serialize_field_basic_field(serialized_example, example):
    assert serialize_field(Example.array, example.array) == serialized_example["array"]


def test_serialize_with_mapper_to_different_keys():
    class Foo(Structure, FastSerializable):
        a = String
        i = Integer

        _serialization_mapper = {"a": "aaa", "i": "iii"}

    create_serializer(Foo)
    foo = Foo(a="string", i=1)

    assert Foo.serialize(foo) == {"aaa": "string", "iii": 1}


def test_serialize_with_deep_mapper_ignores_mappping():
    class Foo(Structure, FastSerializable):
        a = String
        i = Integer

    class Bar(Structure, FastSerializable):
        wrapped = Array[Foo]

        _serialization_mapper = {
            "wrapped._mapper": {"a": "aaa", "i": "iii"},
            "wrapped": "other",
        }

    create_serializer(Foo)
    create_serializer(Bar)

    bar = Bar(wrapped=[Foo(a="string1", i=1), Foo(a="string2", i=2)])
    serialized = Bar.serialize(bar)
    assert serialized == {"other": [{"a": "string1", "i": 1}, {"a": "string2", "i": 2}]}


def test_raise_exception_if_nested_structure_is_not_fastserializable_0():
    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure, FastSerializable):
        wrapped: Foo

    with pytest.raises(TypeError) as excinfo:
        create_serializer(Bar)
    assert "Foo is not FastSerializable or does not implement 'serialize(self, value)'" in str(excinfo.value)

def test_raise_exception_if_nested_structure_is_not_fastserializable_1():
    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure, FastSerializable):
        wrapped: Array[Foo]

    with pytest.raises(TypeError) as excinfo:
        create_serializer(Bar)
    assert "Foo is not FastSerializable or does not implement 'serialize(self, value)'" in str(excinfo.value)


def test_raise_exception_if_nested_structure_is_not_fastserializable_2():

    class Foo(Structure):
        a = String
        i: int

    class Bar(Structure, FastSerializable):
        wrapped: Array[Array[Foo]]

    with pytest.raises(TypeError) as excinfo:
        create_serializer(Bar)
    assert "Foo is not FastSerializable or does not implement 'serialize(self, value)'" in str(excinfo.value)


def test_raise_exception_if_nested_structure_is_does_not_implement_serialize():
    class Foo(Structure, FastSerializable):
        a = String
        i = Integer

    class Bar(Structure, FastSerializable):
        wrapped = Array[Foo]

    with pytest.raises(TypeError) as excinfo:
        create_serializer(Bar)
    assert "Foo is not FastSerializable or does not implement 'serialize(self, value)'"


def test_serialize_with_mappers_in_nested_structures():
    class Foo(Structure, FastSerializable):
        ab_a = String
        ij_i = Integer

        _serialization_mapper = [
            mappers.TO_CAMELCASE,
            mappers.TO_LOWERCASE,
        ]

    class Bar(Structure, FastSerializable):
        foo = Foo
        array = Array

        _serialization_mapper = {"foo": "foo_mapped"}

    class Example(Structure, FastSerializable):
        bar = Bar
        number = Integer

        _serialization_mapper = {"bar": "bar_1"}

    create_serializer(Foo)
    create_serializer(Bar)
    create_serializer(Example)

    example = Example(number=1, bar=Bar(foo=Foo(ab_a="string", ij_i=10), array=[1, 2]))
    serialized = Example.serialize(example)
    assert serialized == {
        "number": 1,
        "bar_1": {"foo_mapped": {"ABA": "string", "IJI": 10}, "array": [1, 2]},
    }


def test_serialize_with_camel_case_setting():
    class Bar(Structure, FastSerializable):
        bar_bar = String

        _serialization_mapper = mappers.TO_LOWERCASE

    class Foo(Structure, FastSerializable):
        a = String
        i_num = Integer
        cba_def_xyz = Integer
        bar = Bar

        _serialization_mapper = mappers.TO_CAMELCASE

    create_serializer(Bar)
    create_serializer(Foo)
    foo = Foo(i_num=5, a="xyz", cba_def_xyz=4, bar=Bar(bar_bar="abc"))
    assert Foo.serialize(foo) == {
        "a": "xyz",
        "iNum": 5,
        "cbaDefXyz": 4,
        "bar": {"BAR_BAR": "abc"},
    }


def test_serialize_with_mapper_with_functions_not_supported():
    class Foo(Structure, FastSerializable):
        function = Function
        i = Integer

        _serialization_mapper = {
            "function": FunctionCall(func=lambda f: f.__name__),
            "i": FunctionCall(func=lambda x: x + 5),
        }

    with raises(ValueError) as excinfo:
        create_serializer(Foo)

    assert "Function mappers is not supported in fast serialization" in str(
        excinfo.value
    )


def test_enum_serialization_returns_string_name():
    class Values(enum.Enum):
        ABC = enum.auto()
        DEF = enum.auto()
        GHI = enum.auto()

    class Example(Structure, FastSerializable):
        arr = Array[Enum[Values]]

    create_serializer(Example)
    e = Example(arr=[Values.GHI, Values.DEF, "GHI"])
    assert Example.serialize(e) == {"arr": ["GHI", "DEF", "GHI"]}


def test_serialization_of_classreference_should_work():
    class Bar(Structure, FastSerializable):
        x = Integer
        y = Integer

    class Foo(Structure, FastSerializable):
        a = Integer
        bar1 = Bar
        bar2 = Bar

        _required = []

    create_serializer(Bar)
    create_serializer(Foo)

    input_dict = {"a": 3, "bar1": {"x": 3, "y": 4, "z": 5}}
    foo = deserialize_structure(Foo, input_dict)
    assert Foo.serialize(foo)["bar1"] == {"x": 3, "y": 4}
    assert Foo.bar1.serialize(foo.bar1) == {"x": 3, "y": 4}


def test_serialize_array_field_directly():
    class Values(enum.Enum):
        ABC = enum.auto()
        DEF = enum.auto()
        GHI = enum.auto()

    class Foo(Structure, FastSerializable):
        arr = Array[Enum[Values]]

    create_serializer(Foo)

    foo = Foo(arr=[Values.ABC, Values.DEF])
    assert Foo.arr.serialize(foo.arr) == ["ABC", "DEF"]


def test_convert_camel_case():
    class Foo(Structure, FastSerializable):
        first_name: String
        last_name: String
        age_years: PositiveInt
        _additionalProperties = False
        _serialization_mapper = mappers.TO_CAMELCASE

    create_serializer(Foo)

    original = Foo(first_name="joe", last_name="smith", age_years=5)
    res = Foo.serialize(original)
    assert res == {"firstName": "joe", "lastName": "smith", "ageYears": 5}


def test_serialization_decimal():
    def quantize(d):
        return d.quantize(Decimal("1.00000"))

    class Foo(Structure, FastSerializable):
        a = DecimalNumber
        s = String

    create_serializer(Foo)

    foo = Foo(a=Decimal("1.11"), s="x")
    result = Foo.serialize(foo)
    assert quantize(Decimal(result["a"])) == quantize(Decimal(1.11))


def test_serialize_field_with_inheritance():
    class Foo(Structure, FastSerializable):
        s: str
        i: int
        d: DateTime
        _required = []

    class Bar(Foo):
        a = Array[str]
        _required = []

    create_serializer(Foo)
    create_serializer(Bar)

    now = datetime.datetime.now()
    bar = Bar(a=["x"], d=now, s="xyz")
    assert Bar.s.serialize(bar.s) == "xyz"
    assert Bar.d.serialize(bar.d) == now.strftime("%m/%d/%y %H:%M:%S")


def test_serialize_mapper_to_lowercase():
    class Bar(Structure, FastSerializable):
        field1 = String
        field2 = String

        _serialization_mapper = mappers.TO_LOWERCASE

    class Foo(Structure, FastSerializable):
        abc = Integer
        m = Map[String, Bar]

        _serialization_mapper = mappers.TO_LOWERCASE

    create_serializer(Bar)
    create_serializer(Foo)

    foo = Foo(abc=123, m={"my_key": Bar(field1="xxx", field2="yyy")})
    serialized = foo.serialize()
    assert serialized == {
        "ABC": 123,
        "M": {"my_key": {"FIELD1": "xxx", "FIELD2": "yyy"}},
    }
    assert Deserializer(Foo).deserialize(serialized) == foo


def test_serialize_anyof():
    class TestSerializable(SerializableField):
        def serialize(self, value):
            return value.rstrip()

        def deserialize(self, value):
            return value + "  "

    class Container(ImmutableStructure, FastSerializable):
        field1: String
        field2: AnyOf[NoneField, TestSerializable]

    create_serializer(Container)

    f = {"field1": "val1", "field2": "val2"}
    f2d = Deserializer(Container).deserialize(f)
    f2s = f2d.serialize()
    assert f2s == f


def test_serialize_optional_of_serializablefield():
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

    create_serializer(Container1)
    create_serializer(Container2)

    f2d = Deserializer(Container2).deserialize(f)
    f2s = Container2.serialize(f2d)
    assert f2s == f

    f1d = Deserializer(Container1).deserialize(f)
    f1s = f1d.serialize()
    assert f1s == f


def test_trivial_serializable():
    class Foo(SerializableField):
        pass

    class Bar(Structure, FastSerializable):
        foo: Foo

    create_serializer(Bar)

    deserialized = Bar(foo=123)
    serialized = {"foo": 123}
    assert Deserializer(Bar).deserialize(serialized) == deserialized
    assert deserialized.serialize() == serialized


def test_serialize_multified_with_any():
    class MyPoint1:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Foo(Structure, FastSerializable):
        a: Array[AnyOf[Integer, MyPoint1]]

    create_serializer(Foo)

    with raises(TypeError) as excinfo:
        Foo.serialize(Foo(a=[1, MyPoint1(1, 2)]))
    assert "Object of type MyPoint1 is not JSON serializable" in str(excinfo.value)


def test_optional_field_defect_234(serialized_example):
    class Number(enum.Enum):
        One = 1
        Two = 2
        Three = 3

    class Foo(Structure, FastSerializable):
        a: Optional[Number]

    class Bar(ImmutableStructure, FastSerializable):
        foo: Foo

    create_serializer(Foo)
    create_serializer(Bar)

    foo = Foo(a=Number.One)
    bar = Bar(foo=foo)
    bar.serialize()

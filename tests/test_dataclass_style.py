import sys

python_ver_atleast_than_37 = sys.version_info[0:2] > (3, 6)
if python_ver_atleast_than_37:
    from dataclasses import dataclass, FrozenInstanceError
    from typing import T
from typing import List, FrozenSet, Dict, Union, Iterable

import pytest
from pytest import raises

from typedpy import AllOf, Enum, Number, Float, Structure, ImmutableStructure
from typedpy import Integer, String, Array, StructureReference


class SimpleStruct(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)


class Example(Structure):
    i: Integer(maximum=10)
    s: String(maxLength=5)
    array = Array[Integer(multiplesOf=5), Number]
    embedded = StructureReference(a1=Integer(), a2=Float())
    simple_struct = SimpleStruct
    all = AllOf[Number, Integer]
    enum = Enum(values=[1, 2, 3])
    _required = []


class MixedTypesExample(Structure):
    i: Integer(maximum=10)
    s: String(maxLength=5)
    s1: str
    a: dict
    simple: SimpleStruct


def test_partially_use_annotation():
    print(Example)
    assert Example(i=9, s="xyz", all=4).i == 9
    assert Example(i=9, s="xyz", all=4).all == 4

    with raises(ValueError):
        Example(i=20, s="xyz")


def test_partially_use_annotation_invalid_value():
    with raises(ValueError):
        Example(i=20, s="xyz")
    with raises(TypeError):
        Example(i=5, s=[])


def test_type_conversion_to_typedpy_signature_error():
    with raises(TypeError) as excinfo:
        MixedTypesExample(i=5, s="xyz", s1="asd", a={'x': 1})
    assert "missing a required argument: 'simple'" in str(excinfo.value)


def test_type_conversion_to_typedpy_str_representation():
    d = MixedTypesExample(i=5, s="xyz", s1="asd", a={'x': 1}, simple=SimpleStruct(name="John"))

    assert str(d) == "<Instance of MixedTypesExample. Properties: a = {x = 1}, i = 5, s = 'xyz', " \
                     "s1 = 'asd', simple = <Instance of SimpleStruct. Properties: name = 'John'>>"
    assert str(MixedTypesExample) == "<Structure: MixedTypesExample. Properties: a = <Map>, " \
                                     "i = <Integer. Properties: maximum = 10>, s = <String. Properties: maxLength = " \
                                     "5>, s1 = <String>, simple = <ClassReference: SimpleStruct>>"


def test_type_conversion_to_typedpy_validation_err_for_converted_type():
    with raises(TypeError) as excinfo:
        MixedTypesExample(i=5, s="xyz", s1="asd", simple=SimpleStruct(name="John"), a="a")
    assert "a: Expected <class 'dict'>" in str(excinfo.value)


def test_type_conversion_to_typedpy_validation_err_for_standard_field():
    with raises(ValueError) as excinfo:
        MixedTypesExample(i=50, s="xyz", s1="asd", a="a", simple=SimpleStruct(name="John"))
    assert "i: Got 50; Expected a maximum of 10" in str(excinfo.value)


def test_all_fields_use_alternate_format():
    class Example1(Structure):
        i: int
        f: float
        mylist: list
        map: dict

    e = Example1(i=1, f=0.5, mylist=['x'], map={'x': 'y'})
    with raises(TypeError) as excinfo:
        e.mylist = 7
    assert "mylist: Got 7; Expected <class 'list'>" in str(excinfo.value)


def test_all_fields_use_alternate_format_immutable():
    class ExampleOfImmutable(ImmutableStructure):
        i: int
        mylist: list
        map: dict

    e = ExampleOfImmutable(i=1, mylist=['x'], map={'x': 'y'})
    with raises(ValueError) as excinfo:
        e.mylist.append('y')
    assert "Field is immutable" in str(excinfo.value)


def test_invalid_default():
    with raises(TypeError) as excinfo:
        class Example(Structure):
            i: int = "x"

    assert "i: Invalid default value: 'x'; Reason: Expected <class 'int'>; Got 'x'" in str(excinfo.value)


def test_default_values():
    class Example(Structure):
        i: int = 5
        mylist: list = [1, 2, 3]
        map: dict
        f: Float = 0.5
        f2 = Float(default=1.5)

    e = Example(map={'x': 'y'})
    assert e.i == 5
    assert e.mylist == [1, 2, 3]
    assert e.map == {'x': 'y'}
    assert e.f == 0.5
    assert e.f2 == 1.5


def test_default_values_use_equals_on_field_instance():
    class Example(Structure):
        f: Float() = 0.5
        map: dict
        arr: Array[SimpleStruct] = [SimpleStruct(name="John")]

    e = Example(map={'x': 'y'})
    assert e.f == 0.5
    assert e.arr[0].name == "John"


def test_default_values_use_equals_on_field_instance_with_overriding_required():
    class Example(Structure):
        f: Float() = 0.5
        map: dict
        arr: Array[SimpleStruct] = [SimpleStruct(name="John")]
        i = Integer(default=5)
        _required = ['arr', i]

    e = Example(map={'x': 'y'})
    assert e.f == 0.5
    assert e.arr[0].name == "John"
    assert e.i == 5


def test_some_default_values_missing_required():
    class Example(Structure):
        i: int = 5
        mylist: list
        map: dict
        f: Float = 0.5
        f2 = Float(default=1.5)

    with raises(TypeError) as excinfo:
        Example(map={'x': 'y'})
    assert "missing a required argument: 'mylist'" in str(excinfo.value)


def test_some_default_values_predefined_required():
    class ExampleOfImmutable(Structure):
        i: int = 5
        mylist: list
        map: dict
        f: Float = 0.5
        f2 = Float(default=1.5)
        _required = ['f2']

    assert ExampleOfImmutable(map={'x': 'y'}).f == 0.5


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_valid_typing_valid1():
    class ExampleWithTyping(Structure):
        mylist: List[List[int]]
        i: Integer(minimum=50)
        myset: FrozenSet

    e = ExampleWithTyping(myset={1, 2, 3}, i=100, mylist=[[1, 2, 3]])
    assert e.mylist[0] == [1, 2, 3]


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_valid_typing_valid2():
    class ExampleWithTyping(Structure):
        mymap: Dict[str, List]
        myset: FrozenSet[int]

    assert str(ExampleWithTyping) == '<Structure: ExampleWithTyping. Properties: mymap = <Map. Properties: items' \
                                     ' = [<String>, <Array>]>, myset = <ImmutableSet. Properties: items = <Integer>>>'
    e = ExampleWithTyping(myset={1, 2, 3}, mymap={"x": [1, 2, 3]})
    assert e.mymap["x"] == [1, 2, 3]


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_typing_error():
    class ExampleWithTyping(Structure):
        mymap: Dict[str, List]

    with raises(TypeError) as exc_info:
        ExampleWithTyping(mymap={"x": 5})
    assert "mymap_value: Got 5; Expected <class 'list'>" in str(exc_info.value)


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_typing_error_in_generic():
    class ExampleWithTyping(Structure):
        i: Integer
        a: List[int]

    with raises(TypeError) as exc_info:
        ExampleWithTyping(i=5, a=[1, 2, 3, "x"])
    assert "a_3: Expected <class 'int'>; Got 'x'" in str(exc_info.value)

@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_typing_error_unsupported():
    with raises(TypeError) as exc_info:
        class ExampleWithTyping(Structure):
            i: Iterable[int]
            a: List[int]
    assert "typing.Iterable[int] type is not supported" in str(exc_info.value)


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_typing_error_in_generic_union_mapps_to_anyof():
    class ExampleWithTyping(Structure):
        a: Union[int, float, str]

    assert str(ExampleWithTyping) == '<Structure: ExampleWithTyping. Properties: ' \
                                     'a = <AnyOf [<Integer>, <Float>, <String>]>>'
    e = ExampleWithTyping(a='x')
    with raises(ValueError) as exc_info:
        e.a = []
    assert "a: [] Did not match any field option" in str(exc_info.value)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.7 or higher")
def test_typing_error_in_generic_pep585_err():
    class ExampleWithTyping(Structure):
        i: Integer
        a: list[int]

    e = ExampleWithTyping(i=5, a=[1, 2, 3])
    assert e.a[0] == 1
    with raises(TypeError) as exc_info:
        e.a[2] = "x"
    assert "a_2: Expected <class 'int'>; Got 'x'" in str(exc_info.value)

    with raises(TypeError) as exc_info:
        ExampleWithTyping(i=5, a=[1, 2, 3, "x"])
    assert "a_3: Expected <class 'int'>; Got 'x'" in str(exc_info.value)


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_valid_typing_and_dataclass():
    @dataclass(frozen=True)
    class ExampleWithTyping(Structure):
        mylist: List[List[int]]
        i: Integer(minimum=50)
        myset: FrozenSet

    e = ExampleWithTyping(myset=frozenset({2, 3}), i=100, mylist=[[1, 2, 3]])
    with raises(FrozenInstanceError):
        e.mylist = frozenset()


def test_invalid_type():
    class Bar: pass

    with raises(TypeError):
        class Foo(Structure):
            a: list[Bar]


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_generic_typevar_is_ignored():
    class Foo(Structure):
        a: List[T]

    assert Foo(a=[1,2]).a[1] == 2
    with raises(TypeError):
        Foo(a=1)
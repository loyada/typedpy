from pytest import raises

from typedpy import AllOf, Enum, Number, Float, Structure
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
    assert Example(i=9, s="xyz", all=4).i==9
    assert Example(i=9, s="xyz", all=4).all==4

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
        MixedTypesExample(i=5, s="xyz", s1="asd",  simple=SimpleStruct(name="John"), a="a")
    assert "a: Expected <class 'dict'>" in str(excinfo.value)


def test_type_conversion_to_typedpy_validation_err_for_standard_field():
    with raises(ValueError) as excinfo:
        MixedTypesExample(i=50, s="xyz", s1="asd", a="a", simple=SimpleStruct(name="John"))
    assert "i: Got 50; Expected a maximum of 10" in str(excinfo.value)


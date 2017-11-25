from pytest import raises

from typedpy import Structure, Tuple, Number, String, Integer, Float, createTypedField

class Foo(object):
    def __init__(self, a=0, b=0):
        self.a = a
        self.b = b


def validate_foo(foo):
    if foo.a + foo.b < 10:
        raise ValueError("a+b must be larger or equal to 10")


FooField = createTypedField("FooField", Foo)
ValidatedFooField = createTypedField("FooField", Foo, validate_func=validate_foo)

class A(Structure):
    _required = []
    a = FooField
    b = ValidatedFooField


def test_wrong_type_err():
    with raises(TypeError) as excinfo:
        A(a=2)
    assert "a: Expected <class 'test_typed_field_creator.Foo'>" in str(excinfo.value)

def test_right_type1():
    assert A(a=Foo(1,2)).a.a == 1

def test_invalid_value_err():
    with raises(ValueError) as excinfo:
        A(b=Foo(1,2))
    assert "a+b must be larger or equal to 10" in str(excinfo.value)

def test_valid_value():
    assert A(b=Foo(3, 8)).b.b==8

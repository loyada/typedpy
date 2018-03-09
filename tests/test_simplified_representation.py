from pytest import raises

from typedpy import Structure, Array, String, Integer

class Example(Structure):
    _required = []
    a = Integer
    b = String
    c = Array[String(minLength=3, pattern='[A-Za-z]+$')]
    d = Array[Integer]
    e = Array[Integer, String]
    f = Array(items = [String, Integer])


def test_Integer_prop_err():
    with raises(TypeError) as excinfo:
        Example(a = 3.3)
    assert "a: Expected <class 'int'>" in str(excinfo.value)

def test_String_prop_err():
    with raises(TypeError) as excinfo:
        Example(b = 3.3)
    assert "b: Expected a string" in str(excinfo.value)

def test_valid_props():
    assert Example(a = 3, b = 'abc').b == 'abc'


def test_array_generics_with_props_err():
    with raises(ValueError) as excinfo:
        Example(c = ['aaa', 'bb'])
    assert "c_1: Expected a minimum length of 3" in str(excinfo.value)

def test_array_generics_with_props_valid():
    assert Example(c = ['aaa', 'bbbb']).c[1] == 'bbbb'

def test_array_generics_without_props_err():
    with raises(TypeError) as excinfo:
        Example(d = [1, 2, 3, 'aa'])
    assert "d_3: Expected <class 'int'>" in str(excinfo.value)

def test_array_generics_without_props_valid():
    assert Example(d = [1, 2, 3]).d == [1,2,3]

def test_array_generics_without_props_update_err():
    e = Example(d = [1, 2, 3])
    with raises(TypeError) as excinfo:
        e.d[1] = []
    assert "d_1: Expected <class 'int'>" in str(excinfo.value)

def test_class_definition_err1():
    with raises(TypeError) as excinfo:
        class Foo(Structure):
            a = Array[int]
    assert "Expected a Field class or instance" in str(excinfo.value)

def test_class_definition_err2():
    with raises(TypeError) as excinfo:
        class Foo(Structure):
            a = Array(items = [int])
    assert "Expected a Field/Structure class or Field instance" in str(excinfo.value)

def test_multiple_items_in_array_schema_definition_err():
    with raises(TypeError) as excinfo:
        class Foo(Structure):
            a = Array[Integer, str]
    assert "Expected a Field class or instance" in str(excinfo.value)

def test_multiple_items_in_array_schema_err():
    with raises(TypeError) as excinfo:
        Example(e=[1,2])
    assert "e_1: Expected a string" in str(excinfo.value)

def test_multiple_items_in_array_schema_valid():
    assert Example(e=[1,'xyz']).e[1] == 'xyz'

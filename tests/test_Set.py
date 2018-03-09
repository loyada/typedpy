from pytest import raises

from typedpy import Structure, Number, String, Integer, Set, AnyOf, Map


class Example(Structure):
    _required = []
    #set support, similar to Array
    b = Set(minItems= 3, maxItems= 5, items = Number(maximum=10))
    d = Set(minItems=2, items = String)
    e = Set(minItems=2)
    f = Set[Integer]
    g = Set[AnyOf(fields = [String(minLength=3), Number(minimum=10)])]



def test_invalid_items_definitions_err1():
    with raises(TypeError) as excinfo:
        class A(Structure):
            a = Set(items = [String, String])
    assert "Expected a Field/Structure class or Field instance" in str(excinfo.value)

def test_invalid_items_definitions_err2():
    with raises(TypeError) as excinfo:
        class A(Structure):
            a = Set[String, String]
    assert "Expected a Field/Structure class or Field instance" in str(excinfo.value)

def test_wrong_type_for_set_items_err():
    with raises(TypeError) as excinfo:
        Example(b = {3, 'aa', 2})
    assert "b: Expected a number" in str(excinfo.value)

def test_list_instead_of_set_err():
    with raises(TypeError) as excinfo:
        Example(b = [3, 'aa', 2])
    assert "b: Expected <class 'set'>" in str(excinfo.value)

def test_set_too_large_err():
    with raises(ValueError) as excinfo:
        Example(b = {1, 2, 3, 4, 5, 6})
    assert "b: Expected length of at most 5" in str(excinfo.value)

def test_set_too_short_err():
    with raises(ValueError) as excinfo:
        Example(b = {1})
    assert "b: Expected length of at least 3" in str(excinfo.value)

def test_right_size_and_Field():
    e = Example(b = {1,2,3,4})
    e.b.add(5)
    assert e.b == {1,2,3,4,5}
    assert 3 in e.b

def test_items_simplified_version_type_err():
    with raises(TypeError) as excinfo:
        Example(d = {1, ''})
    assert "d: Expected a string" in str(excinfo.value)

def test_items_simplified_version_valid():
    with raises(TypeError) as excinfo:
        Example(d = {1, ''})
    assert "d: Expected a string" in str(excinfo.value)

def test_no_items_in_definition():
    e = Example(e={1, 'sadasd', True})
    assert 1 in e.e

def test__super_simplified_definition_type_err():
    with raises(TypeError) as excinfo:
        Example(f={1, 1.5})
    assert "f: Expected <class 'int'>" in str(excinfo.value)

def test_super_simplified_definition_valid():
    e = Example(f={1, 2})
    assert 1 in e.f


def test_simplified_definition_with_flexible_types_valid():
    e = Example(g={10, 'xyz', 45.4})
    assert 'xyz' in e.g

def test_simplified_definition_with_flexible_types_err():
    with raises(ValueError) as excinfo:
        Example(g={'xy'})
    assert "g: Did not match any field option" in str(excinfo.value)

def test_invalid_type():
    with raises(TypeError) as excinfo:
        class Foo(Structure):
            a = Set[Map]
    assert "Set element of type <class 'dict'> is not hashable" in str(excinfo.value)


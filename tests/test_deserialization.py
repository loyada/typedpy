from pytest import raises

from typedpy import Structure, Array, Number, String, Integer, \
    StructureReference, AllOf, deserialize_structure, Enum, \
    Float, TypedField, Map, create_typed_field, AnyOf, Set, Field


class SimpleStruct(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)

class Example(Structure):
    i = Integer(maximum=10)
    s = String(maxLength=5)
    array = Array[Integer(multiplesOf=5), Number]
    embedded = StructureReference(a1 = Integer(), a2=Float())
    simplestruct = SimpleStruct
    all = AllOf[Number, Integer]
    enum = Enum(values=[1,2,3])



def test_successful_deserialization_with_many_types():
    data = {
        'i': 5,
        's': 'test',
        'array': [10, 7],
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'simplestruct': {
            'name': 'danny'
        },
        'all': 5,
        'enum': 3
    }
    example = deserialize_structure(Example, data)
    assert example == Example(
        i = 5,
        s = 'test',
        array = [10,7],
        embedded = {
            'a1': 8,
            'a2': 0.5
        },
        simplestruct = SimpleStruct(name = 'danny'),
        all = 5,
        enum = 3
    )

def test_unsupported_field_err():
    # This has no information about the type - clearly can't deserialize
    class UnsupportedField(Field): pass

    class UnsupportedStruct(Structure):
        unsupported = UnsupportedField

    with raises(NotImplementedError) as excinfo:
        deserialize_structure(UnsupportedStruct, {'unsupported': 1})
    assert "cannot deserialize field 'unsupported'" in str(excinfo.value)


def test_unsupported_nested_field_err():
    class UnsupportedStruct(Structure):
        unsupported = AllOf[Integer, Array]

    with raises(TypeError) as excinfo:
        deserialize_structure(UnsupportedStruct, {'unsupported': 1})
    assert "unsupported: deserialization of Multifield only supports Number, String and Enum" in str(excinfo.value)

def test_invalid_type_err():
    data = {
        'i': 5,
        's': 'test',
        'array': [10, 7],
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'simplestruct': {
            'name': 'danny'
        },
        'all': '',
        'enum': 3,

    }
    with raises(TypeError) as excinfo:
         deserialize_structure(Example, data)
    assert "all: Expected a number" in str(excinfo.value)


def test_invalid_type_err2():
    data = {
        'i': 5,
        's': 'test',
        'array': [10, 7],
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'simplestruct': 2,
        'all': 1,
        'enum': 3,

    }
    with raises(TypeError) as excinfo:
         deserialize_structure(Example, data)
    assert "simplestruct: Expected a dictionary" in str(excinfo.value)



def test_invalid_type_for_array_err():
    data = {
        'i': 5,
        's': 'test',
        'array': 10,
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'simplestruct': {
            'name': 'danny'
        },        'all': 1,
        'enum': 3,

    }
    with raises(TypeError) as excinfo:
         deserialize_structure(Example, data)
    assert "array: Expected <class 'list'>" in str(excinfo.value)


def test_array_has_simgle_itemp_in_definition():
    class Foo(Structure):
        a = Array(items=Integer())

    foo = deserialize_structure(Foo, {'a': [1, 2, -3]})
    assert foo.a[2]==-3


def test_invalid_value_err():
    data = {
        'i': 5,
        's': 'test',
        'array': [10, 7],
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'simplestruct': {
            'name': '123'
        },
        'all': 3,
        'enum': 3,

    }
    with raises(ValueError) as excinfo:
         deserialize_structure(Example, data)
    assert 'name: Does not match regular expression: "[A-Za-z]+$"' in str(excinfo.value)


def test_map_deserialization():
    class Foo(Structure):
        map = Map[Integer, SimpleStruct]

    data = {
        'map': {
            1: {
            'name': 'abc'
            },
            2: {
            'name': 'def'
            }
        }
    }

    example = deserialize_structure(Foo, data)
    assert example.map[1] == SimpleStruct(name = 'abc')
    assert example.map[2] == SimpleStruct(name = 'def')


def test_map_deserialization_type_err():
    class Foo(Structure):
        map = Map[Integer, SimpleStruct]

    data = {
        'map': 5
    }
    with raises(TypeError) as excinfo:
        deserialize_structure(Foo, data)
    assert 'map: expected a dict' in str(excinfo.value)

def test_multifield_with_unsupported_type_err():
    source = {
       'any': 'abc'
    }
    class Foo(Structure):
        any = AnyOf[Map, Set, String]

    with raises(TypeError) as excinfo:
         deserialize_structure(Foo, source)
    assert "any: deserialization of Multifield only supports Number, String and Enum" in str(excinfo.value)


def test_unsupported_type_err():
    source = {
       'bar': 'abc'
    }

    class Bar(object): pass

    WrappedBar = create_typed_field("WrappedBar", Bar)

    class Foo(Structure):
        bar = WrappedBar

    with raises(NotImplementedError) as excinfo:
         deserialize_structure(Foo, source)
    assert "cannot deserialize field 'bar' of type WrappedBar" in str(excinfo.value)


def test_min_items_and_class_reference_err():
    class Foo(Structure):
        a = Integer
        b = Integer

    class Bar(Structure):
        foos = Array(minItems=1, items = Foo)

    serialized = {'foos': [1]}
    with raises(TypeError) as excinfo:
        deserialize_structure(Bar, serialized)
    assert "foos: Expected a dictionary" in str(excinfo.value)


def test_min_items_and_class_reference():
    class Foo(Structure):
        a = Integer
        b = Integer

    class Bar(Structure):
        foos = Array(minItems=1, items = Foo)

    serialized = {'foos': [{'a': 1, 'b': 2}]}
    bar = deserialize_structure(Bar, serialized)
    assert bar.foos[0].b==2

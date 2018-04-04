import json

from pytest import raises

from typedpy import Structure, Array, Number, String, Integer, \
    StructureReference, AllOf, deserialize_structure, Enum, \
    Float, TypedField, serialize, Map, Set, AnyOf, create_typed_field


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
    source = {
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
    example = deserialize_structure(Example, source)
    result = serialize(example)
    assert result==source



def test_map_without_types():
    class Foo(Structure):
        map = Map

    source = {
        'map': {
            'a': 1,
            1: 'b'
        }
    }
    foo = deserialize_structure(Foo, source)
    assert foo.map['a'] == 1


def test_some_empty_fields():
    class Foo(Structure):
        a = Integer
        b = String
        _required = []

    foo = Foo(a=5)
    assert serialize(foo)=={'a': 5}

def test_null_fields():
    class Foo(Structure):
        a = Integer
        b = String
        _required = []

    foo = Foo(a=5, c=None)
    assert serialize(foo)=={'a': 5}


def test_serialize_set():
    class Foo(Structure):
        a = Set()

    foo = Foo(a={1,2,3})
    assert serialize(foo)=={'a': [1,2,3]}

def test_string_field_wrapper_compact():
    class Foo(Structure):
        st = String
        _additionalProperties = False

    foo = Foo(st='abcde')
    assert serialize(foo, compact=True)=='abcde'

def test_string_field_wrapper_not_compact():
    class Foo(Structure):
        st = String
        _additionalProperties = False

    foo = Foo(st='abcde')
    assert serialize(foo, compact=False)=={'st': 'abcde'}


def test_set_field_wrapper_compact():
    class Foo(Structure):
        s = Array[AnyOf[String, Number]]
        _additionalProperties = False

    foo = Foo(s=['abcde', 234])
    assert serialize(foo, compact=True)==['abcde', 234]

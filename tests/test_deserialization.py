from collections import OrderedDict

from pytest import raises

from typedpy import Structure, Array, Number, String, Integer, \
    StructureReference, AllOf, deserialize_structure, Enum, \
    Float, Map, create_typed_field, AnyOf, Set, Field, Tuple, OneOf, Anything, serialize, NotField, \
    SerializableField


class SimpleStruct(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)


class Person(Structure):
    name = String
    ssid = String


class BigPerson(Person):
    height = Integer
    _required = []


class Example(Structure):
    anything = Anything
    i = Integer(maximum=10)
    s = String(maxLength=5)
    any = AnyOf[Array[Person], Person]
    complex_allof = AllOf[AnyOf[Integer, Person], BigPerson]  # this is stupid, but we do it for testing
    people = Array[Person]
    array_of_one_of = Array[OneOf[Float, Integer, Person, StructureReference(a1=Integer(), a2=Float())]]
    array = Array[Integer(multiplesOf=5), OneOf[Array[Person], Number]]
    embedded = StructureReference(a1=Integer(), a2=Float())
    simplestruct = SimpleStruct
    all = AllOf[Number, Integer]
    enum = Enum(values=[1, 2, 3])
    _required = []


"""
    complex test that tests many variations of fields, including various multi-field
"""


def test_successful_deserialization_with_many_types():
    data = {
        'anything': {'a', 'b', 'c'},
        'i': 5,
        's': 'test',
        'complex_allof': {'name': 'john', 'ssid': '123'},
        'array': [10, 7],
        'any': [{'name': 'john', 'ssid': '123'}],
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'people': [{'name': 'john', 'ssid': '123'}],
        'simplestruct': {
            'name': 'danny'
        },
        'array_of_one_of': [{'a1': 8, 'a2': 0.5}, 0.5, 4, {'name': 'john', 'ssid': '123'}],
        'all': 5,
        'enum': 3
    }
    deserialized = deserialize_structure(Example, data)

    expected = Example(
        anything={'a', 'b', 'c'},
        i=5,
        s='test',
        array_of_one_of=[{'a1': 8, 'a2': 0.5}, 0.5, 4, Person(name='john', ssid='123')],
        complex_allof=BigPerson(name='john', ssid='123'),
        any=[Person(name='john', ssid='123')],
        array=[10, 7],
        people=[Person(name='john', ssid='123')],
        embedded={
            'a1': 8,
            'a2': 0.5
        },
        simplestruct=SimpleStruct(name='danny'),
        all=5,
        enum=3
    )
    assert deserialized == expected


def test_successful_deserialization_and_serialization_with_many_types():
    original = {
        'anything': ['a', 'b', 'c'],
        'i': 5,
        's': 'test',
        'complex_allof': {'name': 'john', 'ssid': '123'},
        'array': [10, 7],
        'any': [{'name': 'john', 'ssid': '123'}],
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'people': [{'name': 'john', 'ssid': '123'}],
        'simplestruct': {
            'name': 'danny'
        },
        'array_of_one_of': [{'a1': 8, 'a2': 0.5}, 0.5, 4, {'name': 'john', 'ssid': '123'}],
        'all': 5,
        'enum': 3
    }

    serialized = serialize(deserialize_structure(Example, original))
    sorted_serialized = OrderedDict(sorted(serialized.items()))
    sorted_original = OrderedDict(sorted(original.items()))

    assert sorted_serialized == sorted_original


def test_successful_deserialization_and_serialization_with_many_types1():
    original = {
        'anything': ['a', 'b', 'c'],
        'i': 5,
        's': 'test',
        'complex_allof': {'name': 'john', 'ssid': '123'},
        'array': [10, 7],
        'any': [{'name': 'john', 'ssid': '123'}],
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'people': [{'name': 'john', 'ssid': '123'}],
        'simplestruct': {
            'name': 'danny'
        },
        'array_of_one_of': [{'a1': 8, 'a2': 0.5}, 0.5, 4, {'name': 'john', 'ssid': '123'}],
        'all': 5,
        'enum': 3
    }
    deserialized: Example = deserialize_structure(Example, original)
    deserialized.anything = Person(name="abc", ssid="123123123123123123")

    serialized = serialize(deserialized)
    original['anything'] = {'name': 'abc', 'ssid': '123123123123123123'}
    assert serialized == original


def test_anyof_field_failure():
    data = {
        'i': 5,
        's': 'test',
        'array': [10, 7],
        'any': [{'name': 'john', 'ssid': '123'}, {'name': 'paul'}],
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'people': [{'name': 'john', 'ssid': '123'}],
        'simplestruct': {
            'name': 'danny'
        },
        'all': 5,
        'enum': 3
    }
    with raises(ValueError) as excinfo:
        deserialize_structure(Example, data)
    assert "any: [{'name': 'john', 'ssid': '123'}, {'name': 'paul'}] Did not match any field option" in str(
        excinfo.value)


def test_anyof_field_success():
    class Foo(Structure):
        a = Integer
        b = Array[AnyOf[Person, Float, Array[Person]]]

    data = {
        'a': 1,
        'b': [1.5, [{'name': 'john', 'ssid': '123'}, {'name': 'john', 'ssid': '456'}], {'name': 'john', 'ssid': '789'}],
    }
    deserialized = deserialize_structure(Foo, data)

    expected = Foo(
        a=1,
        b=[
            1.5,
            [Person(name='john', ssid='123'), Person(name='john', ssid='456')],
            Person(name='john', ssid='789')
        ]
    )
    assert deserialized == expected


def test_oneof_field_failure1():
    class Foo(Structure):
        a = Integer
        b = Array[OneOf[String(minLength=3), String(maxLength=5), Integer]]

    data = {'a': 1, 'b': [1, 'abcd']}
    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, data)
    assert "b_1: Matched more than one field option" in str(
        excinfo.value)


def test_oneof_field_failure2():
    class Foo(Structure):
        a = Integer
        b = Array[OneOf[String(minLength=3), String(maxLength=5), Integer]]

    data = {'a': 1, 'b': [1, []]}
    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, data)
    assert "b_1: Did not match any field option" in str(
        excinfo.value)


def test_oneof_field_success():
    class Foo(Structure):
        a = Integer
        b = Array[OneOf[String(minLength=3), String(maxLength=5), Integer]]

    data = {'a': 1, 'b': ['abcdef', 1, 'a', 'b']}
    deserialized = deserialize_structure(Foo, data)

    assert deserialized == Foo(a=1, b=['abcdef', 1, 'a', 'b'])


def test_notfield_field_failure():
    class Foo(Structure):
        a = Integer
        b = Array[NotField[String(minLength=3), String(maxLength=5), Integer]]

    data = {'a': 1, 'b': [1.4, 'abcd']}
    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, data)
    assert "b_1: Expected not to match any field definition" in str(
        excinfo.value)


def test_notfield_field_success():
    class Foo(Structure):
        a = Integer
        b = Array[NotField[String(maxLength=3), Integer(minimum=4)]]

    data = {'a': 1, 'b': ['abcdef', 1, 10.5, []]}
    deserialized = deserialize_structure(Foo, data)

    assert deserialized == Foo(a=1, b=['abcdef', 1, 10.5, []])


def test_unsupported_field_err():
    # This has no information about the type - clearly can't deserialize
    class UnsupportedField(Field): pass

    class UnsupportedStruct(Structure):
        unsupported = UnsupportedField

    with raises(NotImplementedError) as excinfo:
        deserialize_structure(UnsupportedStruct, {'unsupported': 1})
    assert "cannot deserialize field 'unsupported'" in str(excinfo.value)


def test_allof_wrong_value_err():
    class Foo(Structure):
        bar = AllOf[Integer, Array]

    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, {'bar': 1})
    assert "could not deserialize bar: did not match <Array>. reason: bar: must be an iterable" in str(
        excinfo.value)


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
    with raises(ValueError) as excinfo:
        deserialize_structure(Example, data)
    assert "could not deserialize all: did not match <Number>. reason: all: Expected a number" in str(excinfo.value)


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
        }, 'all': 1,
        'enum': 3,

    }
    with raises(ValueError) as excinfo:
        deserialize_structure(Example, data)
    assert "array: must be an iterable" in str(excinfo.value)


def test_array_has_simple_item_in_definition():
    class Foo(Structure):
        a = Array(items=Integer())

    foo = deserialize_structure(Foo, {'a': [1, 2, -3]})
    assert foo.a[2] == -3


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
    assert example.map[1] == SimpleStruct(name='abc')
    assert example.map[2] == SimpleStruct(name='def')


def test_map_deserialization_type_err():
    class Foo(Structure):
        map = Map[Integer, SimpleStruct]

    data = {
        'map': 5
    }
    with raises(TypeError) as excinfo:
        deserialize_structure(Foo, data)
    assert 'map: expected a dict' in str(excinfo.value)


def test_multifield_with_diffrerent_types():
    class Foo(Structure):
        any = AnyOf[Map, Set, String]

    assert deserialize_structure(Foo, {'any': 'abc'}).any == 'abc'
    assert deserialize_structure(Foo, {'any': {'abc': 'def'}}).any['abc'] == 'def'
    assert 'def' in deserialize_structure(Foo, {'any': {'abc', 'def'}}).any


def test_multifield_with_diffrerent_types_no_match():
    class Foo(Structure):
        any = AnyOf[Map, Set, String]

    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, {'any': [1, 2, 3]})
    assert 'any: [1, 2, 3] Did not match any field option' in str(excinfo.value)


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


def test_single_int_deserialization():
    class Foo(Structure):
        i = Integer
        _additionalProperties = False

    data = 5

    example = deserialize_structure(Foo, data)
    assert example.i == 5


def test_single_array_deserialization():
    class Foo(Structure):
        arr = Array[String]
        _additionalProperties = False

    data = ['abc', 'def', 'ghi']

    example = deserialize_structure(Foo, data)
    assert example.arr[2] == 'ghi'


def test_min_items_and_class_reference_err():
    class Foo(Structure):
        a = Integer
        b = Integer

    class Bar(Structure):
        foos = Array(minItems=1, items=Foo)

    serialized = {'foos': [1]}
    with raises(ValueError) as excinfo:
        deserialize_structure(Bar, serialized)
    assert "foos_0: Expected a dictionary" in str(excinfo.value)


def test_min_items_and_class_reference():
    class Foo(Structure):
        a = Integer
        b = Integer

    class Bar(Structure):
        foos = Array(minItems=1, items=Foo)

    serialized = {'foos': [{'a': 1, 'b': 2}]}
    bar = deserialize_structure(Bar, serialized)
    assert bar.foos[0].b == 2


def test_deserialize_tuple():
    class Foo(Structure):
        a = Integer
        t = Tuple[Integer, String]

    serialized = {'a': 3, 't': [3, 'abc']}
    foo = deserialize_structure(Foo, serialized)
    assert foo.t[1] == 'abc'


def test_deserialize_tuple_err():
    class Foo(Structure):
        a = Integer
        t = Tuple[Integer, String]

    serialized = {'a': 3, 't': [3, 4]}
    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, serialized)
    assert "t_1: Expected a string" in str(excinfo.value)


def test_deserialize_set():
    class Foo(Structure):
        a = Integer
        t = Set[Integer]

    serialized = {'a': 3, 't': [3, 4, 3]}
    foo = deserialize_structure(Foo, serialized)
    assert foo.t == {3, 4}


def test_deserialize_inheritance():
    class Blah(Structure):
        x = Integer
        y = Integer

    class Foo(Structure):
        a = Integer
        t = OneOf[Integer, Blah]
        x = String
        _required = ['a']

    class Kah(Foo): pass

    class Bar(Kah):
        b = String

    input_dict = {'a': 3, 't': {'x': 3, 'y': 4}, 'b': '111'}
    bar = deserialize_structure(Bar, input_dict)
    assert bar.t == Blah(x=3, y=4)
    serialized_again = serialize(bar)
    assert OrderedDict(sorted(serialized_again.items())) == OrderedDict(sorted(input_dict.items()))


def test_deserialize_set_err1():
    class Foo(Structure):
        a = Integer
        t = Set[Integer]

    serialized = {'a': 3, 't': 4}
    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, serialized)
    assert "t: must be an iterable" in str(excinfo.value)


def test_deserialize_set_err2():
    class Foo(Structure):
        a = Integer
        t = Set[Integer]

    serialized = {'a': 3, 't': [1, 'asd']}
    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, serialized)
    assert "t_1: Expected <class 'int'>" in str(excinfo.value)


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


def test_serializable_deserialize():
    class MySerializable(Field, SerializableField):
        def __init__(self, *args, some_param="xxx", **kwargs):
            self._some_param = some_param
            super().__init__(*args, **kwargs)

        def deserialize(self, value):
            return {"mykey": "my custom deserialization: {}, {}".format(self._some_param, str(value))}

        def serialize(self, value):
            return 123

    class Foo(Structure):
        d = Array[MySerializable(some_param="abcde")]
        i = Integer

    deserialized = deserialize_structure(Foo, {'d': ["191204", "191205"], 'i': 3})

    assert deserialized == Foo(i=3, d=[{'mykey': 'my custom deserialization: abcde, 191204'},
                                       {'mykey': 'my custom deserialization: abcde, 191205'}])

    assert serialize(deserialized) == {'d': [123, 123], 'i': 3}


def test_deserialization_map():
    class Foo(Structure):
            m1 = Map[String, Anything]
            m2 = Map
            i = Integer

    deserialized = deserialize_structure(Foo, {'m1': {'a': 1, 'b': [1,2,3]},'m2': {1: 2, 'a': 'v'}, 'i': 3})
    assert deserialized.m1['a'] == 1
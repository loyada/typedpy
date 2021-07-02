import enum
import operator
from collections import OrderedDict, deque
from decimal import Decimal

from pytest import raises

from typedpy import Boolean, ImmutableStructure, Structure, Array, Number, String, Integer, \
    StructureReference, AllOf, deserialize_structure, Enum, \
    Float, Map, create_typed_field, AnyOf, Set, Field, Tuple, OneOf, Anything, mappers, serialize, NotField, \
    SerializableField, Deque, PositiveInt, DecimalNumber
from typedpy.serialization import FunctionCall
from typedpy.serialization_wrappers import Deserializer, deserializer_by_discriminator


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
    assert "any: Got [{'name': 'john', 'ssid': '123'}, {'name': 'paul'}]; Does not match any field option" in str(
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
    assert "b_1: Got abcd; Matched more than one field option" in str(
        excinfo.value)


def test_oneof_field_failure2():
    class Foo(Structure):
        a = Integer
        b = Array[OneOf[String(minLength=3), String(maxLength=5), Integer]]

    data = {'a': 1, 'b': [1, []]}
    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, data)
    assert "b_1: Got []; Does not match any field option" in str(
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
    assert "b_1: Got 'abcd'; Expected not to match any field definition" in str(
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
    assert "unsupported: Got 1; Cannot deserialize value of type UnsupportedField" in str(excinfo.value)


def test_allof_wrong_value_err():
    class Foo(Structure):
        bar = AllOf[Integer, Array]

    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, {'bar': 1})
    assert "bar: Got 1; Does not match <Array>. reason: bar: Got 1; Expected a list, set, or tuple" in str(
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
    assert "all: Got ''; Does not match <Number>. reason: all: Got ''; Expected a number" in str(
        excinfo.value)


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
    assert "array: Got 10; Expected a list, set, or tuple" in str(excinfo.value)


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
    assert """name: Got '123'; Does not match regular expression: "[A-Za-z]+$""""" in str(excinfo.value)


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
    assert 'map: Got 5; Expected a dictionary' in str(excinfo.value)


def test_multifield_with_diffrerent_types():
    class Foo(Structure):
        any = AnyOf[Map, Set, String]

    assert deserialize_structure(Foo, {'any': 'abc'}).any == 'abc'
    assert deserialize_structure(Foo, {'any': {'abc': 'def'}}).any['abc'] == 'def'
    assert 'def' in deserialize_structure(Foo, {'any': {'abc', 'def'}}).any


def test_multifield_with_diffrerent_types_no_match():
    class Foo(Structure):
        any = AnyOf[Map, Set[String], String]

    with raises(ValueError) as excinfo:
        deserialize_structure(Foo, {'any': [1, 2, 3]})
    assert 'any: Got [1, 2, 3]; Does not match any field option' in str(excinfo.value)


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
    assert "bar: Got 'abc'; Cannot deserialize value of type WrappedBar." in str(excinfo.value)


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
    assert "t: Got 4; Expected a list, set, or tuple" in str(excinfo.value)


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
    class MySerializable(SerializableField):
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


def test_deserialize_deque():
    class Example(Structure):
        d = Deque[Array]

    original = {'d': [[1, 2], [3, 4]]}
    deserialized = deserialize_structure(Example, original)
    assert deserialized == Example(d=deque([[1, 2], [3, 4]]))
    assert serialize(deserialized) == original


def test_deserialization_map():
    class Foo(Structure):
        m1 = Map[String, Anything]
        m2 = Map
        i = Integer

    deserialized = deserialize_structure(Foo, {'m1': {'a': 1, 'b': [1, 2, 3]}, 'm2': {1: 2, 'a': 'v'}, 'i': 3})
    assert deserialized.m1['a'] == 1


def test_deserialization_non_typedpy_attributes():
    class Foo(Structure):
        m1 = Map[String, Anything]
        m2 = Map
        i = Integer

    deserialized = deserialize_structure(Foo, {'m1': {'a': 1, 'b': [1, 2, 3]}, 'm2': {1: 2, 'a': 'v'}, 'i': 3,
                                               'x': [1, 2, 3]})
    assert deserialized.m1['a'] == 1
    assert deserialized.x == [1, 2, 3]


def test_mapper_variation_1():
    class Foo(Structure):
        m = Map
        s = String
        i = Integer

    mapper = {
        "m": "a",
        "s": FunctionCall(func=lambda x: f'the string is {x}', args=['name'])
    }

    foo = deserialize_structure(Foo,
                                {
                                    'a': {'a': 1, 'b': [1, 2, 3]},
                                    'name': 'Joe',
                                    'i': 3
                                },
                                mapper=mapper,
                                keep_undefined=False)

    assert foo == Foo(i=3, m={'a': 1, 'b': [1, 2, 3]}, s='the string is Joe')


def test_mapper_variation_2():
    class Foo(Structure):
        m = Map
        s = String
        i = Integer

    mapper = {
        "m": "a.b",
        "s": FunctionCall(func=lambda x: f'the string is {x}', args=['name.first']),
        'i': FunctionCall(func=operator.add, args=['i', 'j'])
    }

    foo = deserialize_structure(Foo,
                                {
                                    'a': {'b': {'x': 1, 'y': 2}},
                                    'name': {'first': 'Joe', 'last': 'smith'},
                                    'i': 3,
                                    'j': 4
                                },
                                mapper=mapper,
                                keep_undefined=False)

    assert foo == Foo(i=7, m={'x': 1, 'y': 2}, s='the string is Joe')


class Foo(Structure):
    i: int


class Foo1(Foo):
    a: str


class Foo2(Foo):
    a: int


class Bar(Structure):
    t: str
    f: Array[Integer]
    foo: Foo

    _serialization_mapper = {
        "t": "type",
        "foo": FunctionCall(func=deserializer_by_discriminator({
            "1": Foo1,
            "2": Foo2,
        }),
            args=["type", "x.foo"])
    }


def test_mapper_class_by_discriminator_1():
    serialized = {
        "type": "1",
        "f": [1, 2, 3],
        "x": {
            "foo": {
                "a": "xyz",
                "i": 9
            }
        }
    }
    deserialized = Deserializer(Bar).deserialize(serialized, keep_undefined=False)
    assert deserialized == Bar(t="1", f=[1, 2, 3], foo=Foo1(a="xyz", i=9))


def test_mapper_class_by_discriminator_2():
    serialized = {
        "type": "2",
        "f": [1, 2, 3],
        "x": {
            "foo": {
                "a": 123,
                "i": 9
            }
        }
    }
    deserialized = Deserializer(Bar).deserialize(serialized, keep_undefined=False)
    assert deserialized == Bar(t="2", f=[1, 2, 3], foo=Foo2(a=123, i=9))


def test_mapper_class_by_data_doesnt_match_discriminator():
    serialized = {
        "type": "1",
        "f": [1, 2, 3],
        "x": {
            "foo": {
                "a": 123,
                "i": 9
            }
        }
    }
    with raises(TypeError) as excinfo:
        Deserializer(Bar).deserialize(serialized, keep_undefined=False)
    assert "a: Got 123; Expected a string" in str(
        excinfo.value)


def test_mapper_class_by_discriminator_invalid_discriminator():
    serialized = {
        "type": "3",
        "f": [1, 2, 3],
        "x": {
            "foo": {
                "a": 123,
                "i": 9
            }
        }
    }
    with raises(ValueError) as excinfo:
        Deserializer(Bar).deserialize(serialized, keep_undefined=False)
    assert "discriminator: got '3'; Expected one of ['1', '2']" in str(
        excinfo.value)


def test_mapper_variation_3():
    class Foo(Structure):
        m = Map
        s = String
        i = Integer
        x = Integer

    mapper = {
        "m": "a.b",
        "s": FunctionCall(func=lambda x: f'the string is {x}'),
        'i': FunctionCall(func=lambda x: x * 2)
    }

    foo = deserialize_structure(Foo,
                                {
                                    'a': {'b': {'x': 1, 'y': 2}},
                                    's': 'Joe',
                                    'i': 3,
                                    'x': 5
                                },
                                mapper=mapper,
                                keep_undefined=False)

    assert foo == Foo(i=6, m={'x': 1, 'y': 2}, s='the string is Joe', x=5)


def test_predefined_mapper_case_convert():
    class Bar(Structure):
        i: int
        f: float

    class Foo(Structure):
        abc: str
        xxx_yyy: str
        bar: Bar

        _serialization_mapper = mappers.TO_LOWERCASE

    foo = deserialize_structure(Foo, {'ABC': 'aaa', 'XXX_YYY': 'bbb', 'BAR': {'I': 1, 'F': 1.5}})
    assert foo == Foo(abc='aaa', xxx_yyy='bbb', bar=Bar(i=1, f=1.5))
    assert serialize(foo) == {'ABC': 'aaa', 'XXX_YYY': 'bbb', 'BAR': {'I': 1, 'F': 1.5}}


def test_custom_mapper_keeps_undefined_attributes():
    class Foo(Structure):
        abc: str

        _serialization_mapper = {"abc": "a"}

    foo = deserialize_structure(Foo, {'a': 'x', 'b': 1})
    assert foo == Foo(abc="x", a="x", b=1)


def test_mapper_error1():
    class Foo(Structure):
        m = Map
        s = String
        i = Integer

    mapper = {
        "m": "a.b",
        "s": FunctionCall(func=lambda x: x, args=['name']),
        'i': FunctionCall(func=operator.add, args=['i', 'j'])
    }

    with raises(TypeError) as excinfo:
        deserialize_structure(Foo,
                              {
                                  'a': {'b': {'x': 1, 'y': 2}},
                                  'name': {'first': 'Joe', 'last': 'smith'},
                                  'i': 3,
                                  'j': 4
                              },
                              mapper=mapper,
                              keep_undefined=False)
    assert "s: Got {'first': 'Joe', 'last': 'smith'}; Expected a string" in str(excinfo.value)


def test_mapper_error1():
    class Foo(Structure):
        m = Map
        s = String

    mapper = ['m']

    with raises(TypeError) as excinfo:
        deserialize_structure(Foo,
                              {
                                  'a': {'b': {'x': 1, 'y': 2}},
                                  'name': {'first': 'Joe', 'last': 'smith'},
                                  'i': 3,
                                  'j': 4
                              },
                              mapper=mapper)
    assert "Mapper must be a mapping" in str(excinfo.value)


def test_bad_path_in_mapper():
    class Foo(Structure):
        m = Map
        s = String
        i = Integer

    mapper = {
        "m": "a.x",
        "s": FunctionCall(func=lambda x: x, args=['name']),
        'i': FunctionCall(func=operator.add, args=['i', 'j'])
    }

    with raises(TypeError) as excinfo:
        deserialize_structure(Foo,
                              {
                                  'a': {'b': {'x': 1, 'y': 2}},
                                  'name': {'first': 'Joe', 'last': 'smith'},
                                  'i': 3,
                                  'j': 4
                              },
                              mapper=mapper,
                              keep_undefined=False)
    assert "m: Got None; Expected a dictionary" in str(excinfo.value)


def test_invalid_mapper_value():
    class Foo(Structure):
        m = Map
        s = String
        i = Integer

    mapper = {
        "m": 5,
        "s": FunctionCall(func=lambda x: x, args=['name']),
        'i': FunctionCall(func=operator.add, args=['i', 'j'])
    }

    with raises(TypeError) as excinfo:
        deserialize_structure(Foo,
                              {
                                  'a': {'b': {'x': 1, 'y': 2}},
                                  'name': {'first': 'Joe', 'last': 'smith'},
                                  'i': 3,
                                  'j': 4
                              },
                              mapper=mapper,
                              keep_undefined=False)
    assert "mapper value must be a key in the input or a FunctionCal. Got 5" in str(excinfo.value)


def test_valid_deserializer():
    class Foo(Structure):
        m = Map
        s = String
        i = Integer

    mapper = {
        "m": "a.b",
        "s": FunctionCall(func=lambda x: f'the string is {x}', args=['name.first']),
        'i': FunctionCall(func=operator.add, args=['i', 'j'])
    }

    deserializer = Deserializer(target_class=Foo, mapper=mapper)

    foo = deserializer.deserialize(
        {
            'a': {'b': {'x': 1, 'y': 2}},
            'name': {'first': 'Joe', 'last': 'smith'},
            'i': 3,
            'j': 4
        },
        keep_undefined=False)

    assert foo == Foo(i=7, m={'x': 1, 'y': 2}, s='the string is Joe')


def test_mapper_in_list():
    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure):
        wrapped = Array[Foo]

    mapper = {'wrapped._mapper': {'a': 'aaa', 'i': 'iii'}, 'wrapped': 'other'}
    deserializer = Deserializer(target_class=Bar, mapper=mapper)
    deserialized = deserializer.deserialize(
        {
            'other': [
                {'aaa': 'string1', 'iii': 1},
                {'aaa': 'string2', 'iii': 2}
            ]
        },
        keep_undefined=False)

    assert deserialized == Bar(wrapped=[Foo(a='string1', i=1), Foo(a='string2', i=2)])


def test_mapper_in_embedded_structure():
    class Foo(Structure):
        a = String
        i = Integer
        s = StructureReference(st=String, arr=Array)

    mapper = {'a': 'aaa', 'i': 'iii', 's._mapper':
        {"arr": FunctionCall(func=lambda x: x * 2, args=['xxx'])}}
    deserializer = Deserializer(target_class=Foo, mapper=mapper)
    deserialized = deserializer.deserialize(
        {
            'aaa': 'string',
            'iii': 1,
            's': {'st': 'string', 'xxx': [1, 2, 3]}},
        keep_undefined=False)

    assert deserialized == Foo(a='string', i=1, s={'st': 'string', 'arr': [1, 2, 3, 1, 2, 3]})


def test_deserialize_with_deep_mapper():
    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure):
        foo = Foo
        array = Array

    class Example(Structure):
        bar = Bar
        number = Integer

    mapper = {'bar._mapper': {'foo._mapper': {"i": FunctionCall(func=lambda x: x * 2)}}}
    deserializer = Deserializer(target_class=Example, mapper=mapper)
    deserialized = deserializer.deserialize(
        {
            "number": 1,
            "bar":
                {
                    "foo": {
                        "a": "string",
                        "i": 10
                    },
                    "array": [1, 2]
                }
        },
        keep_undefined=False)
    assert deserialized == Example(number=1, bar=Bar(foo=Foo(a="string", i=20), array=[1, 2]))


def test_deserialize_with_deep_mapper_camel_case():
    class Foo(Structure):
        a_b = String
        i = Integer

    class Bar(Structure):
        foo_bar = Foo
        array_nums = Array

    class Example(Structure):
        bar = Bar
        number = Integer

    mapper = {'bar._mapper': {'fooBar._mapper': {"i": FunctionCall(func=lambda x: x * 2)}}}
    deserializer = Deserializer(target_class=Example, mapper=mapper,
                                camel_case_convert=True)
    deserialized = deserializer.deserialize(
        {
            "number": 1,
            "bar":
                {
                    "fooBar": {
                        "aB": "string",
                        "i": 10
                    },
                    "arrayNums": [1, 2]
                }
        },
        keep_undefined=False)
    assert deserialized == Example(number=1, bar=Bar(foo_bar=Foo(a_b="string", i=20), array_nums=[1, 2]))


def test_serialize_with_camel_case_setting():
    class Foo(Structure):
        a = String
        i_num = Integer
        cba_def_xyz = Integer

        _serialization_mapper = mappers.TO_CAMELCASE

    serialized = {
        "a": "xyz",
        "iNum": 5,
        "cbaDefXyz": 4
    }

    assert Deserializer(Foo).deserialize(serialized) == Foo(i_num=5, a="xyz", cba_def_xyz=4)


def test_deserialize_with_deep_mapper_camel_case_setting():
    class Foo(Structure):
        a_b = String
        i = Integer

    class Bar(Structure):
        foo_bar = Foo
        array_nums = Array

    class Example(Structure):
        bar = Bar
        number = Integer
        _serialization_mapper = mappers.TO_CAMELCASE

    mapper = {'bar._mapper': {'fooBar._mapper': {"i": FunctionCall(func=lambda x: x * 2)}}}
    deserializer = Deserializer(target_class=Example, mapper=mapper)
    deserialized = deserializer.deserialize(
        {
            "number": 1,
            "bar":
                {
                    "fooBar": {
                        "aB": "string",
                        "i": 10
                    },
                    "arrayNums": [1, 2]
                }
        },
        keep_undefined=False)
    assert deserialized == Example(number=1, bar=Bar(foo_bar=Foo(a_b="string", i=20), array_nums=[1, 2]))


def test_deserializer_no_mapper():
    class Foo(Structure):
        m = Map
        s = String
        i = Integer

    deserializer = Deserializer(target_class=Foo)

    foo = deserializer.deserialize({
        'm': {'x': 1},
        's': 'abc',
        'i': 9999})

    assert foo.i == 9999


def test_invalid_deserializer():
    class Foo(Structure):
        m = Map
        s = String
        i = Integer

    mapper = {
        "xyz": "a.b",
        "s": FunctionCall(func=lambda x: f'the string is {x}', args=['name.first']),
        'i': FunctionCall(func=operator.add, args=['i', 'j'])
    }

    with raises(ValueError) as excinfo:
        Deserializer(target_class=Foo, mapper=mapper)
    assert "Invalid key in mapper for class Foo: xyz. Keys must be one of the class fields" in str(excinfo.value)


def test_enum_deserialization_converts_to_enum():
    class Values(enum.Enum):
        ABC = enum.auto()
        DEF = enum.auto()
        GHI = enum.auto()

    class Example(Structure):
        arr = Array[Enum[Values]]

    deserialized = Deserializer(target_class=Example).deserialize({'arr': ['GHI', 'DEF', 'ABC']})
    assert deserialized.arr == [Values.GHI, Values.DEF, Values.ABC]


def test_undefined_attributes_in_embedded_field_should_be_deserialized_correctly():
    class Blah(Structure):
        x = Integer
        y = Integer

    class Foo(Structure):
        a = Integer
        blah = Blah

    input_dict = {'a': 3, 'blah': {'x': 3, 'y': 4, 'z': 5}}
    bar = deserialize_structure(Foo, input_dict)
    assert bar.blah.z == 5


def test_deserialize_with_ignore_nones():
    class Foo(Structure):
        a = String
        m = Map[String, String]
        c = Integer = 5
        _required = ['a']
        _ignore_none = True

    input_dict = {'a': 'abc', 'm': None, 'c': None}
    bar = deserialize_structure(Foo, input_dict)
    assert bar.a == 'abc'
    assert bar.c == 5


def test_deserialize_with_ignore_nones_deep():
    class Blah(Structure):
        x = Integer(default=5)
        y = Integer
        _required = []
        _ignore_none = True

    class Foo(Structure):
        a = Integer
        blah = Blah

    input_dict = {'a': 3, 'blah': {'x': None, 'y': None, 'z': 555}}
    deserialized = deserialize_structure(Foo, input_dict)
    assert deserialized.a == 3
    assert deserialized.blah.x == 5
    assert deserialized.blah.y is None
    assert deserialized.blah.z == 555


def test_convert_camel_case1():
    class Foo(Structure):
        first_name: String
        last_name: String
        age_years: PositiveInt
        _additionalProperties = False

    input_dict = {
        "firstName": "joe",
        "lastName": "smith",
        "ageYears": 5
    }
    res = Deserializer(target_class=Foo, camel_case_convert=True).deserialize(input_dict)
    assert res == Foo(first_name="joe", last_name="smith", age_years=5)


def test_convert_camel_case2():
    class Foo(Structure):
        first_name: String
        last_name: String
        age_years: PositiveInt
        _additionalProperties = False

    input_dict = {
        "first_name": "joe",
        "last_name": "smith",
        "ageYears": 5
    }
    res = Deserializer(target_class=Foo, camel_case_convert=True).deserialize(input_dict)
    assert res == Foo(first_name="joe", last_name="smith", age_years=5)


def test_ignore_node_should_not_work_on_required_fields():
    class Foo(Structure):
        a = Integer
        s = String
        i = Integer
        _required = ["s"]
        _ignore_none = True

    with raises(TypeError) as excinfo:
        Deserializer(target_class=Foo).deserialize({"s": None, "a": None, "i": 1})
    assert "s: Got None; Expected a string" in str(excinfo.value)
    assert Deserializer(target_class=Foo).deserialize({"s": "x", "a": None, "i": 1}).a is None


def test_deserialization_decimal():
    def quantize(d):
        return d.quantize(Decimal('1.00000'))

    class Foo(Structure):
        a = DecimalNumber
        s = String

    foo = Deserializer(target_class=Foo).deserialize({"s": "x", "a": 1.11})
    assert quantize(foo.a) == quantize(Decimal('1.11'))


def test_deserialize_boolean():
    class Foo(ImmutableStructure):
        a: Boolean
        b: Boolean

    foo = Deserializer(Foo).deserialize({"a": True, "b": "True"})
    assert foo == Foo(a=True, b=True)
    assert foo.b is True

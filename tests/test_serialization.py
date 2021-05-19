import enum
import pickle
import sys
from decimal import Decimal

python_ver_atleast_than_37 = sys.version_info[0:2] > (3, 6)
if python_ver_atleast_than_37:
    from dataclasses import dataclass

import pytest
from pytest import raises

from typedpy import Structure, Array, Number, String, Integer, \
    StructureReference, AllOf, deserialize_structure, Enum, \
    Float, serialize, Set, AnyOf, DateField, Anything, Map, Function, PositiveInt, DecimalNumber
from typedpy.extfields import DateTime
from typedpy import serialize_field
from typedpy.serialization import FunctionCall
from typedpy.serialization_wrappers import Serializer, Deserializer


class SimpleStruct(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)


class Point:
    def __init__(self, x, y):
        self._x = x
        self._y = y


class Example(Structure):
    i = Integer(maximum=10)
    s = String(maxLength=5)
    array = Array[Integer(multiplesOf=5), Number]
    embedded = StructureReference(a1=Integer(), a2=Float())
    simple_struct = SimpleStruct
    all = AllOf[Number, Integer]
    enum = Enum(values=[1, 2, 3])
    points = Array[Point]
    _optional = ["points"]


@pytest.fixture()
def serialized_source():
    return {
        'i': 5,
        's': 'test',
        'array': [10, 7],
        'embedded': {
            'a1': 8,
            'a2': 0.5
        },
        'simple_struct': {
            'name': 'danny'
        },
        'all': 5,
        'enum': 3,
    }


@pytest.fixture()
def example(serialized_source):
    return deserialize_structure(Example, serialized_source)


def test_successful_deserialization_with_many_types(serialized_source, example):
    example = deserialize_structure(Example, serialized_source)
    result = serialize(example)
    assert result == serialized_source


def test_deserialization_with_non_typedpy_wrapper_can_be_inconsistent(serialized_source, example):
    serialized_source['points'] = [{'x': 1, 'y': 2}]
    example = deserialize_structure(Example, serialized_source)
    result = serialize(example)
    assert result['points'][0] != serialized_source['points'][0]


def test_some_empty_fields():
    class Foo(Structure):
        a = Integer
        b = String
        _required = []

    foo = Foo(a=5)
    assert serialize(foo) == {'a': 5}


def test_null_fields():
    class Foo(Structure):
        a = Integer
        b = String
        _required = []

    foo = Foo(a=5, c=None)
    assert serialize(foo) == {'a': 5}


def test_serialize_set():
    class Foo(Structure):
        a = Set()

    foo = Foo(a={1, 2, 3})
    assert serialize(foo) == {'a': [1, 2, 3]}


def test_string_field_wrapper_compact():
    class Foo(Structure):
        st = String
        _additionalProperties = False

    foo = Foo(st='abcde')
    assert serialize(foo, compact=True) == 'abcde'


def test_string_field_wrapper_not_compact():
    class Foo(Structure):
        st = String
        _additionalProperties = False

    foo = Foo(st='abcde')
    assert serialize(foo, compact=False) == {'st': 'abcde'}


def test_set_field_wrapper_compact():
    class Foo(Structure):
        s = Array[AnyOf[String, Number]]
        _additionalProperties = False

    foo = Foo(s=['abcde', 234])
    assert serialize(foo, compact=True) == ['abcde', 234]


def test_serializable_serialize_and_deserialize():
    from datetime import date

    class Foo(Structure):
        d = Array[DateField(date_format="%y%m%d")]
        i = Integer

    foo = Foo(d=[date(2019, 12, 4), "191205"], i=3)
    serialized = serialize(foo)
    assert serialized == {'d': ["191204", "191205"], 'i': 3}

    deserialized = deserialize_structure(Foo, serialized)
    assert deserialized == Foo(i=3, d=[date(2019, 12, 4), date(2019, 12, 5)])


def test_serialize_map_without_any_type_definition():
    class Bar(Structure):
        m = Map()
        a = Integer

    original = Bar(a=3, m={'abc': Bar(a=2, m={"x": "xx"}), 'bcd': 2})
    serialized = serialize(original)
    pickled = pickle.dumps(serialized)
    assert type(serialized['m']) == dict
    assert type(serialized['m']['abc']) == dict
    assert type(serialized['m']['abc']['m']) == dict


def test_pickle_with_map_without_any_type_definition():
    class Bar(Structure):
        m = Map()
        a = Integer

    original = Bar(a=3, m={'abc': Bar(a=2, m={"x": "xx"}), 'bcd': 2})
    serialized = serialize(original)
    unpickeled = pickle.loads(pickle.dumps(serialized))
    deserialized = Deserializer(target_class=Bar).deserialize(unpickeled)
    # there is no info on the fact that deserialized.m['abc'] should be converted to a Bar instance, so
    # we convert it to a simple dict, to make it straight forward to compare
    original.m['abc'] = Serializer(original.m['abc']).serialize()
    assert deserialized == original


def test_serializable_serialize_and_deserialize2():
    from datetime import datetime

    class Foo(Structure):
        d = Array[DateTime]
        i = Integer

    atime = datetime(2020, 1, 30, 5, 35, 35)
    atime_as_string = atime.strftime('%m/%d/%y %H:%M:%S')
    foo = Foo(d=[atime, "01/30/20 05:35:35"], i=3)
    serialized = serialize(foo)
    assert serialized == {
        'd': [atime_as_string, '01/30/20 05:35:35'],
        'i': 3}

    deserialized = deserialize_structure(Foo, serialized)
    assert str(deserialized) == str(Foo(i=3, d=[atime, datetime(2020, 1, 30, 5, 35, 35)]))


def test_serializable_serialize_and_deserialize_of_a_non_serializable_value():
    from datetime import datetime

    class Foo(Structure):
        d = DateTime
        i = Integer

    atime = datetime(2020, 1, 30, 5, 35, 35)
    foo = Foo(d=atime, i=3, x=atime)
    with raises(ValueError) as excinfo:
        serialize(foo)
    # this is to cater to Python 3.6
    assert "x: cannot serialize value" in str(excinfo.value)
    assert "not JSON serializable" in str(excinfo.value)


def test_serialize_map():
    class Foo(Structure):
        m1 = Map[String, Anything]
        m2 = Map
        i = Integer

    foo = Foo(m1={'a': [1, 2, 3], 'b': 1}, m2={1: 2, 'x': 'b'}, i=5)
    serialized = serialize(foo)
    assert serialized['m1'] == {'a': [1, 2, 3], 'b': 1}


def test_serialize_field_basic_field(serialized_source, example):
    assert serialize_field(Example.array, example.array) == serialized_source['array']


def test_serialize_wrong_value():
    with raises(TypeError) as excinfo:
        serialize({'abc': 123})
    assert "serialize: Not a Structure or Field that with an obvious serialization." \
           " Got: {'abc': 123}. Maybe try serialize_field() instead?" in str(excinfo.value)


def test_serialize_with_structured_reference(example, serialized_source):
    assert serialize(example.embedded) == serialized_source['embedded']


def test_serialize_with_array(example, serialized_source):
    assert serialize(example.array) == serialized_source['array']


def test_serialize_with_class_reference(example, serialized_source):
    assert serialize(example.simple_struct) == serialized_source['simple_struct']


def test_serialize_with_map():
    class Foo(Structure):
        m = Map[String, Anything]

    original = {'a': [1, 2, 3], 'b': 1}

    foo = Foo(m=original)
    assert serialize(foo.m) == original


def test_serialize_with_anything_field():
    class Foo(Structure):
        m = Map[String, Anything]

    original = {'a': [1, 2, 3], 'b': 1}

    foo = Foo(m=original)
    assert serialize(foo.m) == original


def test_serialize_with_number(example, serialized_source):
    assert serialize(example.i) == serialized_source['i']


def test_serialize_field_complex_field():
    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure):
        x = Float
        foos = Array[Foo]

    bar = Bar(x=0.5, foos=[Foo(a='a', i=5), Foo(a='b', i=1)])
    assert serialize_field(Bar.foos, bar.foos)[0]['a'] == 'a'


def test_serialize_non_typedpy_attribute():
    class Foo(Structure):
        a = String
        i = Integer

    foo = Foo(a='a', i=1)
    foo.x = {'x': 1, 's': 'abc'}
    assert serialize(foo)['x'] == {'x': 1, 's': 'abc'}


def test_serialize_with_mapper_to_different_keys():
    class Foo(Structure):
        a = String
        i = Integer

    foo = Foo(a='string', i=1)
    mapper = {'a': 'aaa', 'i': 'iii'}
    assert serialize(foo, mapper=mapper) == {'aaa': 'string', 'iii': 1}


def test_serialize_with_mapper_to_different_keys_in_array():
    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure):
        wrapped = Array[Foo]

    bar = Bar(wrapped=[Foo(a='string1', i=1), Foo(a='string2', i=2)])
    mapper = {'wrapped._mapper': {'a': 'aaa', 'i': 'iii'}, 'wrapped': 'other'}
    serialized = serialize(bar, mapper=mapper)
    assert serialized == \
           {'other': [{'aaa': 'string1', 'iii': 1}, {'aaa': 'string2', 'iii': 2}]}


def test_serialize_with_deep_mapper():
    class Foo(Structure):
        a = String
        i = Integer

    class Bar(Structure):
        foo = Foo
        array = Array

    class Example(Structure):
        bar = Bar
        number = Integer

    example = Example(number=1,
                      bar=Bar(foo=Foo(a="string", i=5), array=[1, 2])
                      )
    mapper = {'bar._mapper': {'foo._mapper': {"i": FunctionCall(func=lambda x: x * 2)}}}
    serialized = serialize(example, mapper=mapper)
    assert serialized == \
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
           }


def test_serialize_with_deep_mapper_camel_case():
    class Foo(Structure):
        a = String
        i_num = Integer
        c_d = Integer

    class Bar(Structure):
        foo_bar = Foo
        array_one = Array

    class Example(Structure):
        bar = Bar
        number = Integer

    example = Example(number=1,
                      bar=Bar(foo_bar=Foo(a="string", i_num=5, c_d=2), array_one=[1, 2])
                      )
    mapper = {'bar._mapper': {'foo_bar._mapper': {"c_d": "cccc", "i_num": FunctionCall(func=lambda x: x * 2)}}}
    serialized = serialize(example, mapper=mapper, camel_case_convert=True)
    assert serialized == \
           {
               "number": 1,
               "bar":
                   {
                       "fooBar": {
                           "a": "string",
                           "iNum": 10,
                           "cccc": 2
                       },
                       "arrayOne": [1, 2]
                   }
           }


def test_serialize_with_mapper_with_functions():
    def my_func(): pass

    class Foo(Structure):
        function = Function
        i = Integer

    foo = Foo(function=my_func, i=1)
    mapper = {
        'function': FunctionCall(func=lambda f: f.__name__),
        'i': FunctionCall(func=lambda x: x + 5)
    }
    assert serialize(foo, mapper=mapper) == {'function': 'my_func', 'i': 6}


def test_serialize_with_mapper_with_function_converting_types():
    class Foo(Structure):
        num = Float
        i = Integer

    foo = Foo(num=5.5, i=999)
    mapper = {
        'num': FunctionCall(func=lambda f: [int(f)]),
        'i': FunctionCall(func=lambda x: str(x))
    }
    assert serialize(foo, mapper=mapper) == {'num': [5], 'i': '999'}


def test_serialize_with_mapper_with_function_with_args():
    class Foo(Structure):
        f = Float
        i = Integer

    foo = Foo(f=5.5, i=999)
    mapper = {
        'f': FunctionCall(func=lambda f: [int(f)], args=['i']),
        'i': FunctionCall(func=lambda x: str(x), args=['f'])
    }
    assert serialize(foo, mapper=mapper) == {'f': [999], 'i': '5.5'}


def test_serialize_invalid_mapper_type():
    class Foo(Structure):
        i = Integer

    with raises(TypeError) as excinfo:
        serialize(Foo(i=1), mapper=[1, 2])
    assert 'Mapper must be a mapping' in str(excinfo.value)


def test_serialize_with_mapper_error():
    def my_func(): pass

    class Foo(Structure):
        function = Function
        i = Integer

    foo = Foo(function=my_func, i=1)
    mapper = {
        'function': 5,
        'i': FunctionCall(func=lambda x: x + 5)
    }
    with raises(TypeError) as excinfo:
        serialize(foo, mapper=mapper)
    assert 'mapper must have a FunctionCall or a string' in str(excinfo.value)


def test_serializer_with_mapper_with_function_with_args():
    class Foo(Structure):
        f = Float
        i = Integer

    foo = Foo(f=5.5, i=999)
    mapper = {
        'f': FunctionCall(func=lambda f: [int(f)], args=['i']),
        'i': FunctionCall(func=lambda x: str(x), args=['f'])
    }
    assert Serializer(source=foo, mapper=mapper).serialize() == {'f': [999], 'i': '5.5'}


def test_serializer_with_invalid_mapper_key_type():
    class Foo(Structure):
        f = Float
        i = Integer

    foo = Foo(f=5.5, i=999)
    mapper = {
        123: FunctionCall(func=lambda f: [int(f)], args=['i']),
        'i': FunctionCall(func=lambda x: str(x), args=['f'])
    }
    with raises(TypeError) as excinfo:
        Serializer(foo, mapper=mapper)
    assert 'mapper_key: Got 123; Expected a string' in str(excinfo.value)


def test_serializer_with_invalid_mapper_value_type():
    class Foo(Structure):
        f = Float
        i = Integer

    foo = Foo(f=5.5, i=999)
    mapper = {
        'f': 123,
        'i': FunctionCall(func=lambda x: str(x), args=['f'])
    }
    with raises(ValueError) as excinfo:
        Serializer(foo, mapper=mapper)
    assert 'mapper_value: Got 123; Did not match any field option' in str(excinfo.value)


def test_serializer_with_invalid_mapper_key():
    class Foo(Structure):
        f = Float
        i = Integer

    foo = Foo(f=5.5, i=999)
    mapper = {
        'x': FunctionCall(func=lambda f: [int(f)], args=['i']),
        'i': FunctionCall(func=lambda x: str(x), args=['f'])
    }
    with raises(ValueError) as excinfo:
        Serializer(foo, mapper=mapper)
    assert 'Invalid key in mapper for class Foo: x. Keys must be one of the class fields.' in str(excinfo.value)


def test_serializer_with_invalid_function_call_arg():
    class Foo(Structure):
        f = Float
        i = Integer

    foo = Foo(f=5.5, i=999)
    mapper = {
        'f': FunctionCall(func=lambda f: [int(f)], args=['i', 'x']),
        'i': FunctionCall(func=lambda x: str(x), args=['f'])
    }
    with raises(ValueError) as excinfo:
        Serializer(foo, mapper=mapper)
    assert 'Mapper[f] has a function call with an invalid argument: x' in str(excinfo.value)


def test_enum_serialization_returns_string_name():
    class Values(enum.Enum):
        ABC = enum.auto()
        DEF = enum.auto()
        GHI = enum.auto()

    class Example(Structure):
        arr = Array[Enum[Values]]

    e = Example(arr=[Values.GHI, Values.DEF, 'GHI'])
    assert Serializer(e).serialize() == {'arr': ['GHI', 'DEF', 'GHI']}


def test_serialization_of_classreference_should_work():
    class Bar(Structure):
        x = Integer
        y = Integer

    class Foo(Structure):
        a = Integer
        bar1 = Bar
        bar2 = Bar

        _required = []

    input_dict = {'a': 3, 'bar1': {'x': 3, 'y': 4, 'z': 5}}
    foo = deserialize_structure(Foo, input_dict)
    assert Serializer(source=foo.bar1).serialize() == {'x': 3, 'y': 4, 'z': 5}
    s = Serializer(source=foo.bar2)
    assert s.serialize() == None


def test_serialize_enum_field_directly():
    class Values(enum.Enum):
        ABC = enum.auto()
        DEF = enum.auto()
        GHI = enum.auto()

    class Foo(Structure):
        arr = Array[Enum[Values]]

    foo = Foo(arr=[Values.ABC, Values.DEF])
    assert serialize(foo.arr[0]) == 'ABC'


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_serialization_with_implicit_wrappers_best_effort_can_work():
    @dataclass
    class SimplePoint:
        x: int
        y: int

    class Foo(Structure):
        points = Array[SimplePoint]

    foo = Foo(points=[SimplePoint(1, 2), SimplePoint(2, 3)])
    serialized = serialize(foo)
    assert serialized['points'][0] == {"x": 1, "y": 2}
    deserialized = deserialize_structure(Foo, serialized)
    assert deserialized == foo


def test_example_of_transformation():
    class Foo(Structure):
        f = Float
        i = Integer

    class Bar(Structure):
        numbers = Array[Integer]
        s = String

    def transform_foo_to_bar(foo: Foo) -> Bar:
        mapper = {
            'i': FunctionCall(func=lambda f: [int(f)], args=['i']),
            'f': FunctionCall(func=lambda x: str(x), args=['f'])
        }
        deserializer = Deserializer(Bar, {'numbers': 'i', 's': 'f'})
        serializer = Serializer(source=foo, mapper=mapper)

        return deserializer.deserialize(serializer.serialize(), keep_undefined=False)

    assert transform_foo_to_bar(Foo(f=5.5, i=999)) == Bar(numbers=[999], s='5.5')


def test_convert_camel_case():
    class Foo(Structure):
        first_name: String
        last_name: String
        age_years: PositiveInt
        _additionalProperties = False

    original = Foo(first_name="joe", last_name="smith", age_years=5)
    res = Serializer(source=original).serialize(camel_case_convert=True)
    assert res == {
            "firstName": "joe",
            "lastName" : "smith",
            "ageYears": 5
    }


def test_serialization_decimal():
    def quantize(d):
        return d.quantize(Decimal('1.00000'))

    class Foo(Structure):
        a = DecimalNumber
        s = String
    foo = Foo(a=Decimal('1.11'), s="x")
    result = Serializer(source=foo).serialize()
    assert quantize(Decimal(result['a'])) == quantize(Decimal(1.11))

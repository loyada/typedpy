from pytest import raises

from typedpy import Structure, Array, Number, String, Integer, \
    StructureReference, AllOf, deserialize_structure, Enum, \
    Float, serialize, Set, AnyOf, DateField, Anything, Map
from typedpy.extfields import DateTime
from typedpy import serialize_field


class SimpleStruct(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)


class Example(Structure):
    i = Integer(maximum=10)
    s = String(maxLength=5)
    array = Array[Integer(multiplesOf=5), Number]
    embedded = StructureReference(a1=Integer(), a2=Float())
    simple_struct = SimpleStruct
    all = AllOf[Number, Integer]
    enum = Enum(values=[1, 2, 3])


def test_successful_deserialization_with_many_types():
    source = {
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
        'enum': 3
    }
    example = deserialize_structure(Example, source)
    result = serialize(example)
    assert result == source


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


def test_serialize_field_basic_field():
    source = {
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
        'enum': 3
    }
    example = deserialize_structure(Example, source)
    assert serialize_field(Example.array, example.array) == source['array']


def test_serialize_wrong_value():
    with raises(TypeError) as excinfo:
        serialize("foo")
        # this is to cater to Python 3.6
    assert "serialize: must get a Structure. Got: foo" in str(excinfo.value)


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


def test_serialize_with_mapper():
    class Foo(Structure):
        a = String
        i = Integer

    foo = Foo(a='string', i=1)
    mapper = {'a': 'aaa', 'i': 'iii'}
    assert serialize(foo, mapper=mapper) == {'aaa': 'string', 'iii': 1}

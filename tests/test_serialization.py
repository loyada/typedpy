from typedpy import Structure, Array, Number, String, Integer, \
    StructureReference, AllOf, deserialize_structure, Enum, \
    Float, serialize, Set, AnyOf, DateField


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


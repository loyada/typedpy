from pytest import raises

from typedpy import Structure, Array, Number, String, Integer, StructureReference, AllOf, deserialize_structure, Enum, \
    Float, TypedField


class SimpleStruct(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)

class Example(Structure):
    i = Integer(maximum=10)
    s = String(maxLength=5)
    a = Array[Integer(multiplesOf=5), Number]
    foo = StructureReference(a1 = Integer(), a2=Float())
    ss = SimpleStruct
    all = AllOf[Number, Integer]
    enum = Enum(values=[1,2,3])

class UnsupportedField(TypedField):
    _ty = str


class UnsupportedStruct(Structure):
    unsupported = UnsupportedField


def test_successful_deserialization_with_many_types():
    data = {
        'i': 5,
        's': 'test',
        'a': [10, 7],
        'foo': {
            'a1': 8,
            'a2': 0.5
        },
        'ss': {
            'name': 'danny'
        },
        'all': 5,
        'enum': 3
    }
    example = deserialize_structure(Example, data)
    assert example == Example(
        i = 5,
        s = 'test',
        a = [10,7],
        foo = {
            'a1': 8,
            'a2': 0.5
        },
        ss = SimpleStruct(name = 'danny'),
        all = 5,
        enum = 3
    )

def test_unsupported_err():
    with raises(NotImplementedError) as excinfo:
        deserialize_structure(UnsupportedStruct, {'unsupported': 1})
    assert "cannot deserialize field 'unsupported'" in str(excinfo.value)


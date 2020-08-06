import copy

import pytest
from pytest import raises

from typedpy import Structure, Array, Number, String, Integer, \
    StructureReference, AllOf, Enum, \
    Float, Map, AnyOf, Set, OneOf, Anything


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
    set = Set[Person]
    all = AllOf[Number, Integer]
    person_by_label = Map[String, Person]
    enum = Enum(values=[1, 2, 3])
    _required = []


@pytest.fixture
def rich_object_example():
    return Example(
        anything={'a', 'b', 'c'},
        i=5,
        s='test',
        array_of_one_of=[{'a1': 8, 'a2': 0.5}, 0.5, 4, Person(name='john', ssid='123')],
        complex_allof=BigPerson(name='john', ssid='123'),
        any=[Person(name='john', ssid='123')],
        array=[10, 7],
        people=[Person(name='john', ssid='123')],
        set={Person(name='john', ssid='123'), Person(name='john', ssid='234'), Person(name='john', ssid='345')},
        embedded={
            'a1': 8,
            'a2': 0.5
        },
        person_by_label={'aaa': Person(name='john', ssid='123'), 'bbb': Person(name='jack', ssid='234')},
        simplestruct=SimpleStruct(name='danny'),
        all=5,
        enum=3
    )


def test_deepcopy_creates_new_instances(rich_object_example):
    source = rich_object_example
    target = copy.deepcopy(source)
    assert target == source
    target.people[0].name = 'jack'
    assert source.people[0].name == 'john'
    target.anything.add('x')
    assert source.anything == {'a', 'b', 'c'}


def test_copy_creates_shallow_copy(rich_object_example):
    source = rich_object_example
    target = copy.copy(source)
    assert target == source
    target.people[0].name = 'jack'
    assert source.people[0].name == 'jack'
    target.anything.add('x')
    assert source.anything == {'a', 'b', 'c', 'x'}


def test_ne():
    source = Example(
        anything={'a', 'b', 'c'},
        i=5,
        s='test')
    target = copy.copy(source)
    assert target == source
    assert not target != source

    target.i = 3
    assert target != source


def test_dir(rich_object_example):
    assert dir(rich_object_example) == ['all', 'any', 'anything', 'array', 'array_of_one_of', 'complex_allof',
                                        'embedded', 'enum', 'i', 'people', 'person_by_label', 's', 'set',
                                        'simplestruct']


def test_nonzero():
    assert not Example()
    assert Example(i=5)


def test_contains_supported():
    class Foo(Structure):
        s = Map[String, Anything]

        _additionalProperties = False

    f = Foo(s={'xxx': 123, 'yyy': 234, 'zzz': 'zzz'})
    assert 'xxx' in f
    assert 123 not in f


def test_contains_unsupported():
    class Foo(Structure):
        s = Map[String, Anything]
        i = Integer

        _required = ['s']
        _additionalProperties = False

    f = Foo(s={'xxx': 123, 'yyy': 234, 'zzz': 'zzz'})
    with raises(TypeError) as excinfo:
        assert 'xxx' in f
    assert "Foo does not support this operator" in str(excinfo.value)


def test_get_field_by_name():
    class Person(Structure):
        _required = ['ssid']
        name = String(pattern='[A-Za-z]+$', maxLength=8, default='Arthur')
        ssid = String(minLength=3, pattern='[A-Za-z]+$')
        num = Integer(maximum=30, minimum=10, multiplesOf="dd", exclusiveMaximum=False, default=0)
        foo = StructureReference(a=String(), b=StructureReference(c=Number(minimum=10), d=Number(maximum=10)))

    field_by_name = Person.get_all_fields_by_name()

    assert set(field_by_name.keys()) == {'name', 'ssid', 'num', 'foo'}
    ssid_field = field_by_name['ssid']
    assert ssid_field.__class__ is String
    assert ssid_field.pattern == '[A-Za-z]+$'
    assert ssid_field.minLength == 3

import copy

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


def test_deepcopy_creates_new_instances():
    source = Example(
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
    target = copy.deepcopy(source)
    assert target == source
    target.people[0].name = 'jack'
    assert source.people[0].name == 'john'
    target.anything.add('x')
    assert source.anything == {'a', 'b', 'c'}


def test_copy_creates_shallow_copy():
    source = Example(
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
    target = copy.copy(source)
    assert target == source
    target.people[0].name = 'jack'
    assert source.people[0].name == 'jack'
    target.anything.add('x')
    assert source.anything == {'a', 'b', 'c', 'x'}

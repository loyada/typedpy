from pytest import raises
from typedpy import String, Number, Structure, ImmutableField, ImmutableStructure, Array, Map, Integer, ImmutableMap


class ImmutableString(String, ImmutableField): pass


class A(Structure):
    x = Number
    y = ImmutableString


class B(ImmutableStructure):
    _required = []
    x = String
    y = Number
    z = Array[Number]
    m = Map[String, Number]
    m2 = Map[String, Array]
    a = A


class C(Structure):
    x = Number(immutable=False)


def test_mutable_field_updates_are_ok1():
    a = A(x=3, y="abc")
    a.x = 2
    assert a.x == 2


def test_mutable_field_updates_are_ok2():
    c = C(x=3)
    c.x = 2
    assert c.x == 2


def test_immutable_field_updates_err():
    a = A(x=3, y="abc")
    with raises(ValueError) as excinfo:
        a.y = "a"
    assert "y: Field is immutable" in str(excinfo.value)


def test_immutable_structure_updates_err():
    b = B(x="abc", y=3)
    with raises(ValueError) as excinfo:
        b.y = 1
    assert "Structure is immutable" in str(excinfo.value)


def test_immutable_structure_array_updates_err():
    b = B(z=[1, 2, 3])
    with raises(ValueError) as excinfo:
        b.z[1] = 1
    assert "Structure is immutable" in str(excinfo.value)


def test_immutable_structure_map_updates_err():
    b = B(m={'a': 1, 'b': 2})
    with raises(ValueError) as excinfo:
        b.m['c'] = 1
    assert "Structure is immutable" in str(excinfo.value)


def test_nested_object_reference_update():
    xlist = [1, 2, 3]
    b = B(m2={"x": xlist})
    xlist.append(1)
    assert b.m2['x'] == [1, 2, 3]


def test_changing_reference():
    a = A(x=3, y="abc")
    b = B(a=a)
    a.x = 4
    assert a != b.a
    assert b.a.x == 3


def test_changing_reference2():
    class ExampleWithArray(ImmutableStructure):
        a = Array[A]

    a1 = A(x=1, y="abc")
    a2 = A(x=2, y="abc")

    example = ExampleWithArray(a=[a1, a2])
    a1.x += 1
    assert example.a[0] == A(x=1, y="abc")


def test_assessors_provides_defensive_copy():
    class Example(ImmutableStructure):
        arr = Array
        m = Map

    e = Example(arr=[{'x': 1}], m={'x': [1, 2, 3]})
    e.arr[0]['x'] = 2
    e.m['x'][0] = 0
    for k, v in e.m.items():
        v.append(4)
    for v in e.m.values():
        v.append(5)

    assert e == Example(arr=[{'x': 1}], m={'x': [1, 2, 3]})


def test_assessors_blocks_direct_updates_to_map():
    class Example(ImmutableStructure):
        arr = Array
        m = Map

    e = Example(arr=[{'x': 1}], m={'x': [1, 2, 3]})
    with raises(ValueError):
        e.m['x'] = 0
    with raises(ValueError):
        e.m.pop('x')
    with raises(ValueError):
        e.m.update({})
    with raises(ValueError):
        e.m.clear()


def test_assessors_blocks_direct_updates_to_array():
    class Example(ImmutableStructure):
        arr = Array
        m = Map

    e = Example(arr=[{'x': 1}], m={'x': [1, 2, 3]})
    with raises(ValueError):
        e.arr[0] = 0
    with raises(ValueError):
        e.arr.pop(0)
    with raises(ValueError):
        e.arr.remove(0)
    with raises(ValueError):
        e.arr.clear()
    with raises(ValueError):
        e.arr.append(1)
    with raises(ValueError):
        e.arr.extend([])


def test_array_iterator_return_defensive_copies_for_immutables():
    class Example(ImmutableStructure):
        arr = Array
        m = Map

    e = Example(arr=[{'x': 1}], m={'x': [1, 2, 3]})
    for i in e.arr:
        i['x'] = 1000
    assert e.arr == [{'x': 1}]


def test_array_iterator_return_direct_reference_for_mutables():
    class Example(Structure):
        arr = Array
        m = Map

    e = Example(arr=[{'x': 1}], m={'x': [1, 2, 3]})
    for i in e.arr:
        i['x'] = 1000
    assert e.arr == [{'x': 1000}]


def test_map_iterator_return_defensive_copies_for_immutables():
    class Example(ImmutableStructure):
        arr = Array
        m = Map

    e = Example(arr=[{'x': 1}], m={'x': [1, 2, 3]})
    for k,v in e.m.items():
        v.append(4)
    assert e.m == {'x': [1, 2, 3]}


def test_map_iterator_return_direct_reference_for_mutables():
    class Example(Structure):
        arr = Array
        m = Map

    e = Example(arr=[{'x': 1}], m={'x': [1, 2, 3]})
    for k, v in e.m.items():
        v.append(4)
    assert e.m == {'x': [1, 2, 3, 4]}


def test_changing_reference_err1():
    a = A(x=3, y="abc")
    b = B(a=a)
    with raises(ValueError) as excinfo:
        b.a = A(x=3, y="abc")
    assert "Structure is immutable" in str(excinfo.value)


def test_changing_reference_of_field():
    class Foo(ImmutableField, Map): pass

    class ExampleWithImmutableField(Structure):
        foo = Foo[String, Integer]

    original_map = {'a': 1, 'b': 2}
    example = ExampleWithImmutableField(foo=original_map)

    # when we change the content through the reference we have
    original_map['a'] = 100

    # it has no effect on the field value
    assert example.foo['a'] == 1


def test_changing_map_field():
    class ExampleWithImmutableField(Structure):
        foo = ImmutableMap[String, Integer]

    original_map = {'a': 1, 'b': 2}
    example = ExampleWithImmutableField(foo=original_map)
    with raises(ValueError) as excinfo:
        example.foo['c'] = 1
    assert "foo: Field is immutable" in str(excinfo.value)

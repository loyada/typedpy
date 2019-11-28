from pytest import raises

from typedpy import Structure, Number, String, Map, Field, Integer, PositiveInt, Array, Set


class Example(Structure):
    _required = []

    # standard definition: limits on size. key is a number<=10, value is a string
    a = Map(minItems=3, maxItems=5, items=[Number(maximum=10), String()])

    # a slightly simplified representation - not that String has no '()'
    b = Map(items=(Number(maximum=10), String))

    # Limits on size. Key and value can be anything
    c = Map(minItems=3, maxItems=5)

    # terse, Java-generics like: Key is String of size>=3, value is a number
    d = Map[String(minLength=3), Number]

    # terse, Java-generics like, representation: Key is string, value is a number
    e = Map[String, Number]

    # Key is string, value can be anything
    f = Map[String, Field]

    g = Map


def test_invalid_items_definitions_err1():
    with raises(TypeError) as excinfo:
        class A(Structure):
            a = Map(items=[String])
    assert "items is expected to be a list/tuple of two fields" in str(excinfo.value)


def test_invalid_items_definitions_err2():
    with raises(TypeError) as excinfo:
        class A(Structure):
            a = Map(items=String)
    assert "items is expected to be a list/tuple of two fields" in str(excinfo.value)


def test_invalid_items_definitions_err3():
    with raises(TypeError) as excinfo:
        class A(Structure):
            a = Map(items=[String, int])
    assert "Expected a Field/Structure class or Field instance" in str(excinfo.value)


def test_invalid_assignment_err():
    with raises(TypeError) as excinfo:
        Example(a=[])
    assert "a: Expected <class 'dict'>" in str(excinfo.value)


def test_invalid_key_type_err1():
    with raises(TypeError) as excinfo:
        Example(a={1: 'y', 'x2': 'y', 2: 'y'})
    assert "a_key: Expected a number" in str(excinfo.value)


def test_invalid_key_val_err1():
    with raises(ValueError) as excinfo:
        Example(a={1: 'y', 100: 'y', 2: 'y'})
    assert "a_key: Expected a maxmimum of 10" in str(excinfo.value)


def test_invalid_value_type_err1():
    with raises(TypeError) as excinfo:
        Example(a={1: 'y', 3: 7, 2: 'y'})
    assert "a_value: Expected a string" in str(excinfo.value)


def test_dict_too_large_err():
    with raises(ValueError) as excinfo:
        Example(a={1: 'y', 3: 'y', 2: 'y', 4: 'y', 6: 'y', 7: 'y'})
    assert "a: Expected length of at most 5" in str(excinfo.value)


def test_dict_too_small_err():
    with raises(ValueError) as excinfo:
        Example(a={1: 'y', 3: 'y', 1: 'x'})
    assert "a: Expected length of at least 3" in str(excinfo.value)


def test_dict_first_variation_valid():
    assert Example(a={1: 'y', 3: 'y', 4.5: 'x'}).a[4.5] == 'x'


def test_dict_first_variation_update_err():
    e = Example(a={1: 'y', 3: 'y', 4.5: 'x'})
    with raises(ValueError) as excinfo:
        e.a[100] = ''
    assert "a_key: Expected a maxmimum of 10" in str(excinfo.value)


def test_dict_first_variation_update_to_too_large_err():
    e = Example(a={1: 'y', 3: 'y', 4.5: 'x'})
    with raises(ValueError) as excinfo:
        e.a[2] = ''
        e.a[3.5] = ''
        e.a[7] = ''
    assert "a: Expected length of at most 5" in str(excinfo.value)


def test_dict_first_variation_update_to_too_small_err():
    e = Example(a={1: 'y', 3: 'y', 4.5: 'x'})
    with raises(ValueError) as excinfo:
        del e.a[1]
    assert "a: Expected length of at least 3" in str(excinfo.value)


def test_dict_first_variation_updates_valid():
    e = Example(a={1: 'y', 3: 'y', 4.5: 'x'})
    e.a[10] = 'a'
    del e.a[1]
    assert e.a == {3: 'y', 4.5: 'x', 10: 'a'}


def test_dict_item_is_a_tuple_updates_valid():
    e = Example(b={1: 'y', 3: 'y', 4.5: 'x'})
    e.b[10] = 'a'
    del e.b[1]
    assert e.b == {3: 'y', 4.5: 'x', 10: 'a'}


def test_no_items_definition():
    e = Example(c={1: 'y', 'x': 'y', 4.5: 'x'})
    assert e.c == {1: 'y', 'x': 'y', 4.5: 'x'}


def test_no_items_definition_wrong_size_err():
    with raises(ValueError) as excinfo:
        Example(c={'x': 'y', 4.5: 'x'})
    assert "c: Expected length of at least 3" in str(excinfo.value)


def test_simplified_definition_val_type_err():
    with raises(TypeError) as excinfo:
        Example(d={'xyz': 'y', 'abc': 'x'})
    assert "d_value: Expected a number" in str(excinfo.value)


def test_simplified_definition_key_type_err():
    with raises(TypeError) as excinfo:
        Example(d={'xyz': 1, 4.5: 3})
    assert "d_key: Expected a string" in str(excinfo.value)


def test_simplified_definition_with_updates_valid():
    e = Example(d={'xyz': 1, 'abc': 3})
    e.d['def'] = 0
    e.d['abc'] = e.d['abc'] * 2
    del e.d['xyz']
    assert e.d == {'def': 0, 'abc': 6}


def test_super_simplified_definition_val_type_err():
    with raises(TypeError) as excinfo:
        Example(e={'xyz': 'y', 'abc': 'x'})
    assert "e_value: Expected a number" in str(excinfo.value)


def test_super_simplified_definition_key_type_err():
    with raises(TypeError) as excinfo:
        Example(e={'xyz': 1, 4.5: 3})
    assert "e_key: Expected a string" in str(excinfo.value)


def test_super_simplified_definition_with_updates_valid():
    a = Example(e={'xyz': 1, 'abc': 3})
    a.e['def'] = 0
    a.e['abc'] = a.e['abc'] * 2
    a.e.update({'efg': 5})
    del a.e['xyz']
    assert a.e == {'def': 0, 'abc': 6, 'efg': 5}


def test_any_field_is_valid():
    e = Example(f={'xyz': 1, 'abc': 3.33, 'deff': 'a', 'ssss': [], 'dddd': {1, 2}})
    assert e.f['dddd'] == {2, 1}


def test_str():
    st = str(Example)
    assert "a = <Map. Properties: items = [<Number. Properties: maximum = 10>, <String>], maxItems = 5, minItems = 3>" in st
    assert "b = <Map. Properties: items = [<Number. Properties: maximum = 10>, <String>]>" in st
    assert "c = <Map. Properties: maxItems = 5, minItems = 3>" in st
    assert "d = <Map. Properties: items = [<String. Properties: minLength = 3>, <Number>]>" in st
    assert "e = <Map. Properties: items = [<String>, <Number>]" in st


def test_invalid_key_type():
    with raises(TypeError) as excinfo:
        class Foo(Structure):
            a = Map[Map, Integer]
    assert "Key field of type <Map>, with underlying type of <class 'dict'> is not hashable" in str(excinfo.value)


def test_class_reference_keys_find_in_map():
    class Person(Structure):
        name = String
        age = PositiveInt

    class People(Structure):
        ids = Array[String]
        data = Map[Person, Integer]

    people = People(ids=[], data={Person(name="john", age=5): 20})
    assert Person(age=5, name="john") in people.data


def test_class_reference_keys_find_in_map_failure1():
    class Person(Structure):
        name = String
        age = PositiveInt

    class People(Structure):
        ids = Array[String]
        data = Map[Person, Integer]

    people = People(ids=[], data={Person(name="john", age=5): 20})
    assert Person(age=5, name="smith") not in people.data


def test_class_reference_keys_find_in_map_failure2():
    class Person(Structure):
        name = String
        age = PositiveInt

    class People(Structure):
        ids = Array[String]
        data = Map[Person, Integer]

    people = People(ids=[], data={Person(name="john", age=5): 20})
    assert Person(age=5, name="john", extra=3) not in people.data


def test_simple_map_valid():
    assert Example(g={1: 'abc', 'abc': 1}).g['abc'] == 1


def test_simple_map_invalid():
    with raises(TypeError) as excinfo:
        Example(g={1,'a',2})
    assert "g: Expected <class 'dict'>" in str(excinfo.value)


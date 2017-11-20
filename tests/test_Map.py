from pytest import raises

from typedpy import Structure, Number, String, Map


class Example(Structure):
    _required = []
    a = Map(minItems=3, maxItems=5, items=[Number(maximum=10), String()])
    b = Map(items=(Number(maximum=10), String))
    c = Map(minItems=3, maxItems=5)
    d = Map[String(minLength=3), Number]
    e = Map[String, Number]


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
    assert "Expected a Field class or instance" in str(excinfo.value)



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
    assert Example(a={1: 'y', 3: 'y', 4.5: 'x'}).a[4.5]=='x'


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
    assert e.a == { 3: 'y', 4.5: 'x', 10: 'a'}


def test_dict_item_is_a_tuple_updates_valid():
    e = Example(b={1: 'y', 3: 'y', 4.5: 'x'})
    e.b[10] = 'a'
    del e.b[1]
    assert e.b == { 3: 'y', 4.5: 'x', 10: 'a'}


def test_no_items_definition():
    e = Example(c={1: 'y', 'x': 'y', 4.5: 'x'})
    assert e.c == {1: 'y', 'x': 'y', 4.5: 'x'}


def test_no_items_definition_wrong_size_err():
    with raises(ValueError) as excinfo:
        Example(c={ 'x': 'y', 4.5: 'x'})
    assert "c: Expected length of at least 3" in str(excinfo.value)


def test_simplified_definition_val_type_err():
    with raises(TypeError) as excinfo:
        Example(d={ 'xyz': 'y', 'a': 'x'})
    assert "d_value: Expected a number" in str(excinfo.value)

def test_simplified_definition_key_type_err():
    with raises(TypeError) as excinfo:
        Example(d={ 'xyz': 1, 4.5: 3})
    assert "d_key: Expected a string" in str(excinfo.value)

def test_simplified_definition_with_updates_valid():
    e = Example(d={ 'xyz': 1, 'abc': 3})
    e.d['def'] = 0
    e.d['abc'] = e.d['abc'] *2
    del e.d['xyz']
    assert e.d == { 'def': 0, 'abc': 6}



def test_super_simplified_definition_val_type_err():
    with raises(TypeError) as excinfo:
        Example(e={ 'xyz': 'y', 4.5: 'x'})
    assert "e_value: Expected a number" in str(excinfo.value)

def test_super_simplified_definition_key_type_err():
    with raises(TypeError) as excinfo:
        Example(e={ 'xyz': 1, 4.5: 3})
    assert "e_key: Expected a string" in str(excinfo.value)

def test_super_simplified_definition_with_updates_valid():
    a = Example(e={ 'xyz': 1, 'abc': 3})
    a.e['def'] = 0
    a.e['abc'] = a.e['abc'] *2
    a.e.update({'efg': 5})
    del a.e['xyz']
    assert a.e == { 'def': 0, 'abc': 6, 'efg': 5}





from pytest import raises

from typedpy import Structure, Tuple, Number, String, Integer, Float


class Example(Structure):
    _additionalProperties = True
    _required = []
    # array support, similar to json schema
    a = Tuple(uniqueItems=True, items=[String, String])
    b = Tuple(items=[String, String, Number(maximum=10)])
    c = Tuple[Integer, String, Float]
    d = Tuple[Integer]


def test_wrong_type_for_tuple_err():
    with raises(TypeError) as excinfo:
        Example(a=2)
    assert "a: Got 2; Expected <class 'tuple'>" in str(excinfo.value)


def test_wrong_type_for_tuple_items_err1():
    with raises(TypeError) as excinfo:
        Example(a=('aa', 2))
    assert "a_1: Got 2; Expected a string" in str(excinfo.value)


def test_wrong_type_for_tuple_items_err2():
    with raises(TypeError) as excinfo:
        Example(c=(1, 'aa', 2))
    assert "c_2: Expected <class 'float'>" in str(excinfo.value)


def test_wrong_value_for_tuple_item_err():
    with raises(ValueError) as excinfo:
        Example(b=('aa', 'bb', 92))
    assert "b_2: Got 92; Expected a maximum of 10" in str(excinfo.value)


def test_wrong_length_for_tuple_items_err():
    with raises(ValueError) as excinfo:
        Example(a=('aa',))
    assert "a: Got ('aa',); Expected a tuple of length 2" in str(excinfo.value)


def test_non_unique_items_err():
    with raises(ValueError) as excinfo:
        Example(a=('aa', 'aa'))
    assert "a: Got ('aa', 'aa'); Expected unique items" in str(excinfo.value)


def test_unique_items_valid():
    assert Example(a=('aa', 'bb')).a == ('aa', 'bb')


def test_bad_items_definition_err():
    with raises(TypeError) as excinfo:
        Tuple(items=str)
    assert "Expected a list/tuple of Fields or a single Field" in str(excinfo.value)


def test_simplified_definition_valid_assignment():
    assert Example(c=(1, 'bb', 0.5)).c[1:] == ('bb', 0.5)


def test_wrong_type_in_items_definition_err():
    with raises(TypeError) as excinfo:
        Tuple(items=[int, String])
    assert "Expected a Field class or instance" in str(excinfo.value)


def test_single_type_tuple():
    e = Example(d=(1, 2))
    assert e.d[0] == 1
    assert e.d == (1, 2)


def test_single_type_tuple_err1():
    with raises(TypeError) as excinfo:
        Example(d=(3, 2, 'asdasd'))
    assert "d_2: Expected <class 'int'>" in str(excinfo.value)

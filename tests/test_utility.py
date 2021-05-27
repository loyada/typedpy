from typing import List

from pytest import raises
from typedpy import get_list_type, type_is_generic


def test_get_list_type_valid():
    assert get_list_type(list[int]) == (list, int)


def test_get_list_type_valid_err():
    with raises(TypeError):
        get_list_type(int)


def test_is_generic_yes():
    assert type_is_generic(dict[int, int])
    assert type_is_generic(List[str])
    assert type_is_generic(list[list])


def test_is_generic_false():
    assert not type_is_generic(int)
    assert not type_is_generic(test_get_list_type_valid)
    assert not type_is_generic(list)

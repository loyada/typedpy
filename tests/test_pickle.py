import enum
import pickle

import pytest
from pytest import raises

from typedpy import Integer, String, Array, Map, Structure, Set, Enum, StructureReference, Anything, DateField, \
    ImmutableStructure


class Values(enum.Enum):
    ABC = enum.auto()
    DEF = enum.auto()
    GHI = enum.auto()


class Foo(Structure):
    m = Map


class Example(Structure):
    i = Integer
    s = String
    anything = Anything
    arr = Array[String(maxLength=10)]
    arr2 = Array[Foo]
    map1 = Map[String, Array[Integer]]
    map2 = Map[String, Foo]
    bar = Set
    enum_arr = Array[Enum[Values]]
    date = DateField(date_format="%y%m%d")
    _required = []


class ImmutableExample(ImmutableStructure):
    i = Integer
    s = String
    anything = Anything
    arr = Array[String(maxLength=10)]
    arr2 = Array[Foo]
    map1 = Map[String, Array[Integer]]
    map2 = Map[String, Foo]
    bar = Set
    enum_arr = Array[Enum[Values]]
    date = DateField(date_format="%y%m%d")
    _required = []


@pytest.fixture()
def original_object():
    return Example(
        i=5,
        s="abc",
        arr=['aa', 'bb'],
        anything=Foo(m={1: 1, 2: 2}),
        arr2=[Foo(m={1: 1, 2: 2})],
        map1={'x': [1, 2], 'y': [3, 4]},
        map2={'x': Foo(m={1: 1, 2: 2})},
        bar={2, 3, 2, 4},
        date='191204',
        enum_arr=["ABC", "DEF", "ABC"])


@pytest.fixture()
def original_immutable_object():
    return ImmutableExample(
        i=5,
        s="abc",
        arr=['aa', 'bb'],
        anything=Foo(m={1: 1, 2: 2}),
        arr2=[Foo(m={1: 1, 2: 2})],
        map1={'x': [1, 2], 'y': [3, 4]},
        map2={'x': Foo(m={1: 1, 2: 2})},
        bar={2, 3, 2, 4},
        date='191204',
        enum_arr=["ABC", "DEF", "ABC"])


def test_complex_pickle(original_object):
    pickled = pickle.dumps(original_object)
    unpickled = pickle.loads(pickled)
    assert unpickled == original_object


def test_complex_pickle_of_immutable(original_immutable_object):
    pickled = pickle.dumps(original_immutable_object)
    unpickled = pickle.loads(pickled)
    assert unpickled == original_immutable_object


def test_pickle_maintains_field_definition_validations(original_object):
    unpickled = pickle.loads(pickle.dumps(original_object))
    with raises(TypeError) as ex:
        unpickled.arr.append(5)
    assert "arr_2: Got 5; Expected a string" in str(ex.value)

    with raises(ValueError) as ex:
        unpickled.arr[0]="1234567890123"
    assert "arr_0: Got '1234567890123'; Expected a maximum length of 10" in str(ex.value)


def test_pickle_is_like_deepcopy(original_object):
    unpickled = pickle.loads(pickle.dumps(original_object))
    unpickled.arr.append("xyz")
    assert unpickled.arr == ["aa", "bb", "xyz"]
    assert original_object.arr == ["aa", "bb"]


def test_structure_reference_is_unsupported():
    class Bar(Structure):
        s = StructureReference(a=Integer)

    with raises(TypeError) as excinfo:
        pickle.dumps(Bar(s={'a': 1}))
    assert "s: StructuredReference Cannot be pickled" in str(excinfo.value)

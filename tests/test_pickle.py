import enum
import pickle

from pytest import raises

from typedpy import Integer, String, Array, Map, Structure, Set, Enum, StructureReference, Float, Anything, DateField


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
    arr = Array[String]
    arr2 = Array[Foo]
    map1 = Map[String, Array[Integer]]
    map2 = Map[String, Foo]
    bar = Set
    enum_arr = Array[Enum[Values]]
    date = DateField(date_format="%y%m%d")
    _required = []


def test_complex_pickle():
    original = Example(
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
    print(original.__getstate__())
    unpickled = pickle.loads(pickle.dumps(original))
    assert unpickled == original


def test_structure_reference_is_unsupported():
    class Bar(Structure):
        s = StructureReference(a=Integer)

    with raises(TypeError) as excinfo:
        pickle.dumps(Bar(s={'a': 1}))
    assert "s: StructuredReference Cannot be pickled" in str(excinfo.value)

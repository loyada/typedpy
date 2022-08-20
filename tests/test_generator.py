import pickle

from pytest import raises

from typedpy import Structure, serialize
from typedpy import Generator


class Foo(Structure):
    g: Generator


def test_generator_wrong_type():
    with raises(TypeError):
        Foo(g=[])


def test_generator():
    foo = Foo(g=(i for i in range(5)))
    assert sum(foo.g) == 10


def test_generator_err():
    foo = Foo(g=(i for i in range(5)))
    with raises(TypeError):
        pickle.dumps(foo)
    with raises(TypeError):
        serialize(foo)

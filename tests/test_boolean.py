from pytest import raises

from typedpy import Structure


def test_invalid_boolean():
    class Foo(Structure):
        b: bool

    with raises(TypeError) as excinfo:
        Foo(b=5)
        # this is to cater to Python 3.6
    assert "b: Expected <class 'bool'>; Got 5" in str(excinfo.value)

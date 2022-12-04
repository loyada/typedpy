from datetime import datetime, timedelta

from pytest import raises

from typedpy import Integer, Structure


class Foo(Structure):
    i: int


def test_or_operator_structmeta_and_structure_class():
    class Bar(Structure):
        a: Integer | Foo

    assert Bar(a=5).a == 5
    assert Bar(a=Foo(i=4)).a.i == 4
    with raises(ValueError):
        Bar(a="xxx")


def test_or_operator_structmeta_and_python_type():
    class Blah(Structure):
        a: Integer | str

    assert Blah(a="xxx").a == "xxx"

    with raises(TypeError):

        class Bad(Structure):
            a: Integer | timedelta


def test_or_operator_chain_3():
    class Chain(Structure):
        a: Integer(maximum=100) | Foo | str

    assert Chain(a=Foo(i=5)).a.i == 5
    assert Chain(a="xxx").a == "xxx"
    assert Chain(a=13).a == 13


def test_or_with_literals_valid():
    class Chain(Structure):
        a: Integer(maximum=100) | Foo | "xyz" | 3000

    assert Chain(a=Foo(i=5)).a.i == 5
    assert Chain(a="xyz").a == "xyz"
    assert Chain(a=3000).a == 3000


def test_or_with_literals_invalid():
    class Chain(Structure):
        a: Integer(maximum=100) | Foo | "xyz" | 3000

    with raises(ValueError):
        Chain(a="xxx")
    with raises(ValueError):
        Chain(a=2999)

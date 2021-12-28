from typing import Optional

from typedpy import Structure, nested


class A(Structure):
    i: int


class B(Structure):
    a: Optional[A]


class C(Structure):
    b: Optional[B]


class D(Structure):
    c: Optional[C]


def test_get_nested_attr_ok():
    d = D(c=C(b=B(a=A(i=5))))
    assert nested(lambda: d.c.b.a.i) == 5


def test_get_nested_attr_none():
    d = D(c=C())
    assert nested(lambda: d.c.b.a.i) is None


def test_get_nested_attr_override_default():
    d = D(c=C())
    assert nested(lambda: d.c.b.a.i, default=[]) == []


def test_get_nested_attr_list():
    d = D(c=C())
    d.c.foo = [1, 2, 3]
    assert nested(lambda: d.c.foo[100]) is None
    assert nested(lambda: d.c.foo[2]) == 3
    assert nested(lambda: d.c.foo[2].a) is None
    assert nested(lambda: d.c.foo[100], 99) == 99

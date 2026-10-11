from datetime import date, datetime

from pytest import raises

from typedpy import Boolean, Structure


def test_boolean_string_assignment():
    class Foo(Structure):
        a: Boolean

    foo = Foo(a="False")
    assert foo.a is False
    foo.a = "True"
    assert foo.a is True


def test_datetime():
    class Foo(Structure):
        d: date
        t: datetime

    now = datetime.now()
    foo = Foo(d=now.date(), t=now)
    assert foo.d == now.date()
    assert foo.t == now
    foo.d = str(foo.d)
    assert foo.d == now.date()
    with raises(TypeError) as excinfo:
        foo.t = 123

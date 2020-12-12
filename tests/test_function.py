
from pytest import raises

from typedpy import Structure, Function, Integer, String


class B(Structure):
    e = Function
    i = Integer


def test_integer_instead_of_function_error():
    with raises(TypeError) as excinfo:
        B(e=-5, i=5)
    assert "e: Got -5; Expected a function" in str(excinfo.value)


def test_callable_but_not_a_function_error():
    with raises(TypeError) as excinfo:
        B(e=String, i=5)
    assert "e: Got <class 'typedpy.fields.String'>; Expected a function" in str(excinfo.value)


def test_proper_function():
    def func(a,b): return a*b

    b = B(e=func, i=5)
    assert b.e(3,2) == 6


def test_lambda():
    b = B(e=lambda x,y: x*y, i=5)
    assert b.e(3,2) == 6


def test_builtin_function():
    assert B(e=open, i=5).e == open


def test_method():
    class Foo:
        def bar(self): pass

    assert B(e=Foo.bar, i=5).e == Foo.bar


def test_bound_method():
    class Foo:
        def bar(self): pass

    foo = Foo()
    assert B(e=foo.bar, i=5).e == foo.bar


# note: not all decorators are functions
def test_decorator_which_is_a_function():
    from functools import lru_cache

    assert B(e=lru_cache, i=5).e == lru_cache



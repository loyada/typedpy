from typedpy.extfields import DateField
from typedpy import Structure, DecimalNumber, String, Array, standard_readable_error_for_typedpy_exception, Positive

from pytest import raises

from typedpy.errors import ErrorInfo


class PositiveDecimal(DecimalNumber, Positive): pass

class Foo(Structure):
    a = DecimalNumber
    b = DecimalNumber(maximum=100, multiplesOf=5)
    c = PositiveDecimal
    d = DateField
    arr = Array(items=String, minItems=1)
    _optional = ["d"]
    _additionalProperties = False


def test_error_1():
    with raises(Exception) as ex:
        Foo(a=1, b=10, c=1.1, arr=['abc', 1])
    assert standard_readable_error_for_typedpy_exception(ex.value) == \
           ErrorInfo(field='arr_1', problem='Expected a string', value='1')


def test_error_2():
    with raises(Exception) as ex:
        Foo(a=1, b=10, c=1.1, arr=2)
    assert standard_readable_error_for_typedpy_exception(ex.value) == \
           ErrorInfo(field='arr', problem='Expected an array', value='2')


def test_error_3():
    with raises(Exception) as ex:
        Foo(a=1, b=10, c=1.1)
    assert standard_readable_error_for_typedpy_exception(ex.value) == \
           ErrorInfo(problem="missing a required argument: 'arr'")


def test_error_4():
    with raises(Exception) as ex:
        Foo(a=1, b=10, c=1.1, arr=[])
    assert standard_readable_error_for_typedpy_exception(ex.value) == \
           ErrorInfo(field='arr', problem='Expected length of at least 1', value='[]')


def test_error_5():
    with raises(Exception) as ex:
        Foo(a=1, b=1000, c=1.1, arr=["a"])
    assert standard_readable_error_for_typedpy_exception(ex.value) == \
           ErrorInfo(field='b', problem='Expected a maximum of 100', value='1000')


def test_error_6():
    with raises(Exception) as ex:
        Foo(a=1, b=100, c=1.1, arr=["a"], d="xyz")
    print(standard_readable_error_for_typedpy_exception(ex.value))
    assert standard_readable_error_for_typedpy_exception(ex.value) == \
           ErrorInfo(field="d", problem="time data 'xyz' does not match format '%Y-%m-%d'", value="'xyz'")


def test_error_7():
    with raises(Exception) as ex:
        Foo(a=1, b=100, c=1.1, arr=["a"], e=5)
    assert standard_readable_error_for_typedpy_exception(ex.value) == \
           ErrorInfo(problem="got an unexpected keyword argument 'e'")


def test_real_world_usage():
    try:
        Foo(a=1, b=10, c=1.1, arr=['abc', 1])
    except Exception as ex:
        assert standard_readable_error_for_typedpy_exception(ex) == \
           ErrorInfo(field='arr_1', problem='Expected a string', value='1')

from datetime import datetime

from pytest import raises

from typedpy import String , Structure, ImmutableField, DateString


class ImmutableString(String, ImmutableField): pass

class B(Structure):
    s = String(maxLength=5, minLength=2)
    a = ImmutableString()


def test_max_length_violation_err():
    with raises(ValueError) as excinfo:
        B(s = 'abcdef', a='')
    assert "s: Expected a maxmimum length of 5" in str(excinfo.value)


def test_min_length_violation_err():
    with raises(ValueError) as excinfo:
        B(s = 'a', a='')
    assert "s: Expected a minimum length of 2" in str(excinfo.value)


def test_immutable_err():
    b = B(s='sss', a='asd')
    with raises(ValueError) as excinfo:
        b.a = 'dd'
    assert "a: Field is immutable" in str(excinfo.value)


def test_date_err():
    class Example(Structure):
        d = DateString
    with raises(ValueError) as excinfo:
         Example(d='2017-99-99')
    assert "d: time data '2017-99-99' does not match format" in str(excinfo.value)

def test_date_valid():
    class Example(Structure):
        d = DateString
    e = Example(d='2017-8-9')
    assert datetime.strptime(e.d, '%Y-%m-%d').month==8


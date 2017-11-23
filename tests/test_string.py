from pytest import raises

from typedpy import String , Structure, ImmutableField, ImmutableStructure

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


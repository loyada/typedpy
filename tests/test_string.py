from pytest import raises

from typedpy import String , Structure


class B(Structure):
    s = String(maxLength=5, minLength=2)


def test_max_length_violation_err():
    with raises(ValueError) as excinfo:
        B(s = 'abcdef')
    assert "s: Expected a maxmimum length of 5" in str(excinfo.value)


def test_min_length_violation_err():
    with raises(ValueError) as excinfo:
        B(s = 'a')
    assert "s: Expected a minimum length of 2" in str(excinfo.value)


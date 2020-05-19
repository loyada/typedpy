from pytest import raises

from typedpy import Integer, Structure


class B(Structure):
    e = Integer(minimum = 0, maximum = 10, exclusiveMaximum=True)


def test_exclusive_max_violation_err():
    with raises(ValueError) as excinfo:
        B(e = 10)
    assert "e: Got 10; Expected a maximum of less than 10" in str(excinfo.value)


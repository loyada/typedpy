from pytest import raises

from typedpy import Sized, Structure


class B(Structure):
    s = Sized(maxlen=5)

def test_max_length_violation_err():
    with raises(ValueError) as excinfo:
        B(s = {1,2,3,4,5,6})
    assert "s: Too long" in str(excinfo.value)


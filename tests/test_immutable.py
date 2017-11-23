from pytest import raises
from typedpy import String , Number, Structure, ImmutableField, ImmutableStructure

class ImmutableString(String, ImmutableField): pass

class A(Structure):
    x = Number
    y = ImmutableString


class B(ImmutableStructure):
    x = String
    y = Number


class C(Structure):
    x = Number(immutable=False)


def test_mutable_field_updates_are_ok1():
    a = A(x = 3, y = "abc")
    a.x = 2
    assert a.x == 2


def test_mutable_field_updates_are_ok2():
    c = C(x = 3)
    c.x = 2
    assert c.x == 2


def test_immutable_field_updates_err():
    a = A(x=3, y="abc")
    with raises(ValueError) as excinfo:
        a.y = "a"
    assert "y: Field is immutable" in str(excinfo.value)


def test_immutable_structure_updates_err():
    b = B(x = "abc", y = 3)
    with raises(ValueError) as excinfo:
        b.y = 1
    assert "y: Field is immutable" in str(excinfo.value)


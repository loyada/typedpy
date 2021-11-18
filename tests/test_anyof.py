from pytest import raises

from typedpy import AnyOf, Structure


def test_empty_definition_err():
    with raises(TypeError) as excinfo:

        class Foo(Structure):
            any: AnyOf(fields=[])

    assert "AnyOf definition must include at least one field option" in str(
        excinfo.value
    )

from typedpy import Structure
from pytest import raises


def test_dont_block_unknown_consts(unblock_unknown_consts):
    class Foo(Structure):
        a: int

        _ignore_nonnes = True

    # no exception thrown


def test_block_unknown_consts_default_config():
    with raises(ValueError) as excinfo:

        class Foo(Structure):
            a: int

            _asdasd = True

    assert "attribute _asdasd is not a valid TypedPy attribute." in str(
        excinfo.value
    )


def test_block_unknown_consts(block_unknown_consts):
    with raises(ValueError) as excinfo:

        class Foo(Structure):
            a: int

            _ignore_nonnes = True

    assert "attribute _ignore_nonnes is not a valid TypedPy attribute." in str(
        excinfo.value
    )


def test_block_unknown_consts_method(block_unknown_consts):
    class Foo(Structure):
        a: int

        def aaa(self):
            pass

    # no exception thrown


def test_block_unknown_consts_annotation_is_considered_invalid_field_name(
    block_unknown_consts,
):
    with raises(ValueError) as excinfo:

        class Foo(Structure):
            a: int

            _ignore_nonnes: bool = True

    assert "_ignore_nonnes: invalid field name" in str(excinfo.value)


def test_allow_attribute_starting_with_custom_marker_and_annotation(
    block_unknown_consts,
):
    class Foo(Structure):
        a: int

        _custom_attribute_ignore_nonnes: bool = True

    assert Foo._custom_attribute_ignore_nonnes is True


def test_allow_attribute_starting_with_custom_marker(block_unknown_consts):
    class Foo(Structure):
        a: int

        _custom_attribute_ignore_nonnes = True

    assert Foo._custom_attribute_ignore_nonnes is True

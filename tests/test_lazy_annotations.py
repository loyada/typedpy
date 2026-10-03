# Do NOT add "from __future__ import annotations" to this module.
# These tests cover the default annotations behavior, which is lazy from Python 3.14
# (PEP 649/749): the class namespace contains an annotate function instead of
# "__annotations__".
import enum
import sys

import pytest

from typedpy import Integer, String, Structure, keys_of
from typedpy.commons import get_own_annotations

MODULE_LEVEL_ANNOTATED: int = 3


class Role(enum.Enum):
    admin = 1
    sales = 2


class Foo(Structure):
    i: Integer
    s: str = "abc"


def test_annotated_fields_are_validated():
    with pytest.raises(TypeError) as excinfo:
        Foo(i="not an int")
    assert "i: Expected <class 'int'>; Got 'not an int'" in str(excinfo.value)


def test_annotated_fields_are_class_attributes():
    assert isinstance(Foo.i, Integer)
    assert isinstance(Foo.s, String)
    assert set(Foo.get_all_fields_by_name()) == {"i", "s"}


def test_annotated_defaults():
    assert Foo(i=5).s == "abc"
    with pytest.raises(TypeError):
        Foo(i=5, s=3)


def test_annotations_are_available_after_class_creation():
    assert set(Foo.__annotations__) == {"i", "s"}


def test_annotation_can_use_local_name():
    PositiveInt = Integer(minimum=1)

    class Bar(Structure):
        i: PositiveInt

    assert Bar(i=5).i == 5
    with pytest.raises(ValueError):
        Bar(i=0)


def test_undefined_name_in_annotation_fails_on_class_definition():
    with pytest.raises(NameError):

        class Bar(Structure):  # noqa: F841
            i: NoSuchType  # noqa: F821


def test_keys_of_with_annotated_fields():
    @keys_of(Role)
    class Complete(Structure):
        admin: int
        sales: int

    with pytest.raises(TypeError) as excinfo:

        @keys_of(Role)
        class Incomplete(Structure):  # noqa: F841
            admin: int

    assert "missing fields: sales" in str(excinfo.value)


def test_get_own_annotations_of_plain_class_and_module():
    class Plain:
        a: int
        b: "SomeForwardRef"  # noqa: F821

    assert get_own_annotations(Plain) == {"a": int, "b": "SomeForwardRef"}
    module = sys.modules[__name__]
    assert get_own_annotations(module) == {"MODULE_LEVEL_ANNOTATED": int}
    assert get_own_annotations(module.__dict__) == {"MODULE_LEVEL_ANNOTATED": int}

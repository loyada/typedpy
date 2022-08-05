import enum
from datetime import datetime
from enum import auto

import pytest

from typedpy import Structure
from typedpy.structures.keysof import keys_of


class FirstEnum(enum.Enum):
    aaa = auto()
    bbb = auto()
    ccc = auto()


class SecondEnum(enum.Enum):
    ccc = auto()
    ddd = auto()
    eee = auto()


def test_keys_of_single_enum_correct():
    @keys_of(FirstEnum)
    class Foo(Structure):  # noqa
        aaa: int
        bbb: int
        ccc: int
        another: str

        _required = []

    # This is valid, so nothing is expected

    # verify decorator did not mess up the class
    assert Foo().__class__.__name__ == "Foo"


def test_keys_of_invalid_param():
    with pytest.raises(TypeError) as excinfo:

        @keys_of(datetime)
        class Foo(Structure):  # noqa
            aaa: int
            bbb: int
            ccc: int
            another: str

    assert "keys_of requires enum classes as parameters;" in str(excinfo.value)


def test_keys_of_single_enum_missing_fields():
    with pytest.raises(TypeError) as excinfo:

        @keys_of(FirstEnum)
        class Foo(Structure):  # noqa
            aaa: int
            ccc: int
            another: str

    assert "Foo: missing fields: bbb" in str(excinfo.value)


def test_keys_of_multiple_enums_missing_fields():
    with pytest.raises(TypeError) as excinfo:

        @keys_of(FirstEnum, SecondEnum)
        class Foo(Structure):  # noqa
            aaa: int
            bbb: int
            ddd: str
            another: str

    assert "Foo: missing fields: ccc, eee" in str(excinfo.value)


def test_keys_of_multiple_enums_valid():
    @keys_of(FirstEnum, SecondEnum)
    class Foo(Structure):  # noqa
        aaa: int
        bbb: int
        ddd: str
        ccc: dict
        eee: set
        another: str

    # This is valid, so nothing is expected

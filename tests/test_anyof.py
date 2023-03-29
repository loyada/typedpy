from typing import Optional
from decimal import Decimal
from pytest import raises

from typedpy import AnyOf, ImmutableStructure, OneOf, Structure


def test_empty_definition_err():
    with raises(TypeError) as excinfo:

        class Foo(Structure):
            any: AnyOf(fields=[])

    assert "AnyOf definition must include at least one field option" in str(
        excinfo.value
    )




def test_error_message_for_AnyOf():
    class Foo(ImmutableStructure):
        bar: Optional[int]

    with raises(ValueError) as excinfo:
        Foo(bar=Decimal(123))

    assert ("Foo.bar: 123 of type Decimal Did not match any field option. Valid types are: int, None"
            in str(excinfo.value))





def test_error_message_for_OneOf():
    class Foo(ImmutableStructure):
        bar: OneOf[int, list, str]

    with raises(ValueError) as excinfo:
        Foo(bar=Decimal(123))

    assert ("Foo.bar: 123 of type Decimal Did not match any field option. Valid types are: int, list, str."
            in str(excinfo.value))
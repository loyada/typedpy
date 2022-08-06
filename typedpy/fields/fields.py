"""
Definitions of various types of fields. Supports JSON draft4 types.
"""
import typing
from functools import reduce

from typedpy.commons import wrap_val
from typedpy.structures import ClassReference, Field, StructMeta, TypedField


def _map_to_field(item):
    item = item[0] if isinstance(item, (list, tuple)) and len(item) == 1 else item
    if isinstance(item, StructMeta) and not isinstance(item, Field):
        return ClassReference(item)
    if item in [None, ""] or isinstance(item, Field):
        return item
    elif Field in getattr(item, "__mro__", []):
        return item()
    else:
        raise TypeError("Expected a Field/Structure class or Field instance")


class StructureClass(TypedField):
    _ty = StructMeta


class Generator(TypedField):
    """
    A Python generator. Not serializable.
    """

    _ty = typing.Generator


def verify_type_and_uniqueness(the_type, value, name, has_unique_items):
    if not isinstance(value, the_type):
        raise TypeError(f"{name}: Got {wrap_val(value)}; Expected {str(the_type)}")
    if has_unique_items:
        unique = reduce(
            lambda unique_vals, x: unique_vals.append(x) or unique_vals
            if x not in unique_vals
            else unique_vals,
            value,
            [],
        )
        if len(unique) < len(value):
            raise ValueError(f"{name}: Got {wrap_val(value)}; Expected unique items")

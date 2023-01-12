from functools import wraps
from typing import Type

from typedpy.commons import Constant, first_in
from typedpy.fields import Boolean, FunctionCall, Number, String
from typedpy.structures import ClassReference
from typedpy.serialization.mappers import (
    aggregate_serialization_mappers,
)
from typedpy.structures import (
    Structure,
)


class FastSerializable:
    def serialize(self) -> dict:
        cls_name = self.__class__.__name__
        raise NotImplementedError(
            f"You need to implement serialize(self) for class {cls_name}, or use: create_serializer({cls_name})"
        )


def _get_value(field, cls):
    owner = cls

    def wrapped(self):
        return field.__get__(self, owner)  # pylint: disable=unnecessary-dunder-call

    return wrapped


def _get_serialize(field, cls):
    obj = field._ty if isinstance(field, ClassReference) else field
    owner = cls

    def wrapped(self):
        val = field.__get__(self, owner)  # pylint: disable=unnecessary-dunder-call
        return obj.serialize(val) if val is not None else None

    return wrapped


def _get_constant(constant: Constant):
    def wrapped(_self):
        constant()

    return wrapped


def create_serializer(cls: Type[Structure], compact: bool = False):
    mapper = aggregate_serialization_mappers(cls)
    field_by_name = cls.get_all_fields_by_name()
    processed_mapper = {}
    for field_name, field in field_by_name.items():
        mapped_key = mapper[field_name]
        if mapped_key.__class__ is str:
            if isinstance(field, (Number, String, Boolean)):
                processed_mapper[mapped_key] = _get_value(field, cls)
            else:
                processed_mapper[mapped_key] = _get_serialize(field, cls)
        elif isinstance(mapped_key, (FunctionCall,)):
            raise ValueError("Function mappers is not supported in fast serialization")
        elif isinstance(mapped_key, Constant):
            processed_mapper[field_name] = _get_constant(mapped_key)
    items = processed_mapper.items()

    def serializer(self):
        return {name: value(self) for name, value in items}

    cls.serialize = serializer

    if compact:
        set_compact_wrapper(cls)


def set_compact_wrapper(cls):
    func = cls.serialize

    @wraps(func)
    def wrapper(self: Structure):
        res = func(self)
        if len(self.__class__.get_all_fields_by_name()) == 1 and len(res) == 1:
            return first_in(res.values())
        return res

    cls.serialize = wrapper

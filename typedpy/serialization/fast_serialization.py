from typing import Type

from typedpy import Boolean, ClassReference, Constant, FunctionCall, Number, String
from typedpy.serialization.mappers import (
    aggregate_serialization_mappers,
)
from typedpy.structures import (
    Structure,
)


def _get_value(field, cls):
    owner = cls

    def wrapped(self):
        return field.__get__(self, owner)

    return wrapped


def _get_serialize(field, cls):
    obj = field._ty if isinstance(field, ClassReference) else field
    owner = cls

    def wrapped(self):
        val = field.__get__(self, owner)
        return obj.serialize(val) if val is not None else None

    return wrapped


def _get_constant(constant: Constant):
    def wrapped(_self):
        constant()

    return wrapped


def create_serializer(cls: Type[Structure]):
    mapper = aggregate_serialization_mappers(cls)
    field_by_name = cls.get_all_fields_by_name()
    processed_mapper = {}
    for field_name, field in field_by_name.items():
        mapped_key = mapper[field_name]
        if type(mapped_key) == str:
            if isinstance(field, (Number, String, Boolean)):
                processed_mapper[mapped_key] = _get_value(field, cls)
            else:
                processed_mapper[mapped_key] = _get_serialize(field, cls)
        elif isinstance(mapped_key, (FunctionCall,)):
            raise ValueError("Function mappers is not supported for fast serialization")
        elif isinstance(mapped_key, Constant):
            processed_mapper[field_name] = _get_constant(mapped_key)
    items = processed_mapper.items()

    def serializer(self):
        return {name: value(self) for name, value in items}

    cls.serialize = serializer

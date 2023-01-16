from functools import wraps
from typing import Type

from typedpy.commons import Constant, deep_get, first_in
from typedpy.fields import Boolean, FunctionCall, Number, String
from typedpy.structures import ClassReference
from typedpy.serialization.mappers import (
    aggregate_deserialization_mappers,
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



def _get_deserialize(field):
    obj = field._ty if isinstance(field, ClassReference) else field

    def wrapped(val):
        return obj.deserialize(val) if val is not None else None

    return wrapped


def _get_constant(constant: Constant):
    def wrapped(_self):
        return constant()

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
                processed_mapper[mapped_key] = (
                    _get_constant(field)
                    if isinstance(field, Constant)
                    else _get_serialize(field, cls)
                )
        elif isinstance(mapped_key, (FunctionCall,)):
            raise ValueError("Function mappers is not supported in fast serialization")
        else:
            raise NotImplementedError()
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


def _get_by_mapped_key(mapped_key):
    use_deep_get = "." in mapped_key

    def wrapped(self, input: dict):
        return (
            deep_get(input, mapped_key) if use_deep_get else input.get(mapped_key, None)
        )

    return wrapped


def create_deserializer(cls: Type[Structure]):
    mapper = aggregate_deserialization_mappers(cls)
    field_by_name = cls.get_all_fields_by_name()
    processed_mapper = {}
    for field_name, field in field_by_name.items():
        mapped_key = mapper[field_name]
        if mapped_key.__class__ is str:
            if isinstance(field, (Number, String, Boolean)):
                processed_mapper[field_name] = _get_by_mapped_key(mapped_key=mapped_key)
            else:
                processed_mapper[field_name] = _get_serialize(field, cls)
        elif isinstance(mapped_key, (FunctionCall,)):
            raise ValueError("Function mappers is not supported in fast serialization")

    items = processed_mapper.items()

    def deserializer(input_data):
        return cls(**{name: value(input_data) for name, value in items})

    cls.deserialize = deserializer


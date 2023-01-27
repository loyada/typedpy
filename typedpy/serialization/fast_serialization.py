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
    def __init__(self, *args, **kwargs):
        if not hasattr(self.__class__, "serialize"):
            create_serializer(self.__class__)
        super().__init__(*args, **kwargs)



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
        return constant()

    return wrapped


def create_serializer(cls: Type[Structure], compact: bool = False, serialize_none: bool = False):
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

    items = processed_mapper.items()

    def serializer(self):
        res = {name: value(self) for name, value in items}
        return res if serialize_none else {k:v for (k,v) in res.items() if v is not None}

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

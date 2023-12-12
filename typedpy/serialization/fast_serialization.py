from functools import wraps
from typing import Type

from typedpy.commons import Constant, first_in, Undefined, UndefinedMeta
from typedpy.fields import Boolean, FunctionCall, Number, String, Array, AnyOf, OneOf
from typedpy.structures import ClassReference, Field, NoneField, Structure
from typedpy.structures.structures import (
    created_fast_serializer,
    failed_to_create_fast_serializer,
)

from .mappers import (
    aggregate_serialization_mappers,
)
from ..structures.consts import ENABLE_UNDEFINED


class FastSerializable:
    def __init__(self, *args, **kwargs):
        if (
            "serialize" not in self.__class__.__dict__
            or self.__class__.serialize is FastSerializable.serialize
        ):
            create_serializer(self.__class__)
        super().__init__(*args, **kwargs)

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


def _verify_is_fast_serializable(field):
    obj = field._ty if isinstance(field, ClassReference) else field
    if isinstance(field, Array) and isinstance(field.items, (Field, ClassReference)):
        _verify_is_fast_serializable(field.items)

    if isinstance(field, ClassReference):
        if not issubclass(obj, FastSerializable):
            raise TypeError(
                f"{obj.__name__} is not FastSerializable or does not implement 'serialize(self, value)'"
            )
        if getattr(
            obj, "serialize", None
        ) is FastSerializable.serialize and not getattr(
            obj, failed_to_create_fast_serializer, False
        ):
            create_serializer(obj)


def _get_serialize(field, cls):
    _verify_is_fast_serializable(field)
    obj = field._ty if isinstance(field, ClassReference) else field
    if isinstance(obj, OneOf):
        raise TypeError(f"{obj} Field is not FastSerializable")
    if isinstance(obj, AnyOf):
        non_null = [f for f in getattr(obj, "_fields") if not isinstance(f, NoneField)]
        if len(non_null) > 1:
            raise TypeError(
                f"AnyOf(i.e. Union) is not FastSerializable when it can be multiple types: {obj}"
            )
    owner = cls

    def wrapped(self):
        val = field.__get__(self, owner)  # pylint: disable=unnecessary-dunder-call
        return obj.serialize(val) if val is not None else None

    return wrapped


def _get_constant(constant: Constant):
    def wrapped(_self):
        return constant()

    return wrapped


def create_serializer(
    cls: Type[Structure],
    compact: bool = False,
    serialize_none: bool = False,
    mapper: dict = None,
):
    mapper = mapper or aggregate_serialization_mappers(cls)
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
            raise ValueError("Function mappers are not supported in fast serialization")

    items = processed_mapper.items()

    with_undefined = getattr(cls, ENABLE_UNDEFINED, False)
    has_additional_properties = hasattr(cls, "_additional_serialization")

    def serializer(self):
        res = {name: value(self) for name, value in items}
        filtered_res = (
            {name: value for name, value in res.items() if value is not Undefined}
            if with_undefined
            else res
        )
        res = (
            filtered_res
            if serialize_none
            else {k: v for (k, v) in filtered_res.items() if v is not None}
        )
        if has_additional_properties:
            res.update(self._additional_serialization())

        return res

    cls.serialize = serializer

    if compact:
        set_compact_wrapper(cls)

    setattr(cls, created_fast_serializer, True)


def set_compact_wrapper(cls):
    func = cls.serialize

    @wraps(func)
    def wrapper(self: Structure):
        res = func(self)
        if len(self.__class__.get_all_fields_by_name()) == 1 and len(res) == 1:
            return first_in(res.values())
        return res

    cls.serialize = wrapper

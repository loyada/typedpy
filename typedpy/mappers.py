"""
Module for custom deserialization mappers aggregation
"""
from collections.abc import Mapping
from enum import Enum, auto

from .commons import deep_get
from .structures import ClassReference, Field, Structure, SERIALIZATION_MAPPER
from .fields import Array, FunctionCall, Set, StructureReference


class Constant:
    """
    Mark a value as constant in a versioned mapper.
    This is useful if an attribute did not exist in a previous version
    and you want to assign it to a default value in the more recent version.
    """

    def __init__(self, val):
        self._val = val

    def __call__(self, *args, **kwargs):
        return self._val


class Deleted:
    """
    Used to mark an attribute as "removed" in a versioned mapper.
    This is unsupported (nor needed) in a "regular" serialization mapper.
    """

    pass


# pylint:disable=protected-access, missing-function-docstring, invalid-name
def _set_base_mapper_no_op(cls, for_serialization):
    mapper = {}
    for k, field_def in cls.get_all_fields_by_name().items():
        if isinstance(field_def, ClassReference):
            val = (
                aggregate_serialization_mappers(field_def._ty)
                if for_serialization
                else aggregate_deserialization_mappers(field_def._ty)
            )
            mapper[f"{k}._mapper"] = val
        elif isinstance(field_def, (Array, Set)):
            items = (
                [field_def.items]
                if isinstance(field_def.items, Field)
                else field_def.items
                if isinstance(field_def.items, list)
                else []
            )
            values = {}
            for i in items:
                if isinstance(i, ClassReference):
                    val = (
                        aggregate_serialization_mappers(i._ty)
                        if for_serialization
                        else aggregate_deserialization_mappers(i._ty)
                    )
                    values.update(val)
                elif isinstance(i, StructureReference):
                    val = (
                        aggregate_serialization_mappers(i._newclass)
                        if for_serialization
                        else aggregate_deserialization_mappers(i._newclass)
                    )
                    values.update(val)
            if values:
                mapper[f"{k}._mapper"] = values

        elif isinstance(field_def, StructureReference):
            val = (
                aggregate_serialization_mappers(field_def._newclass)
                if for_serialization
                else aggregate_deserialization_mappers(field_def._newclass)
            )
            mapper[f"{k}._mapper"] = val
        mapper[k] = k

    return mapper


def _convert_to_camelcase(key):
    words = key.split("_")
    return words[0] + "".join(w.title() for w in words[1:])


def _convert_to_snakecase(key):
    return "".join(
        ["_" + char.lower() if char.isupper() else char for char in key]
    ).lstrip("_")


def _apply_mapper(
    latest_mapper, key, previous_mapper, for_serialization, is_self=False
):
    val = key if is_self else previous_mapper[key]
    if latest_mapper == mappers.TO_CAMELCASE:
        return _convert_to_camelcase(val)
    if latest_mapper == mappers.TO_LOWERCASE:
        return val.upper()
    latest_mapper_val = latest_mapper.get(val, val)
    if isinstance(latest_mapper_val, (FunctionCall,)):
        args = (
            [(deep_get(previous_mapper, k) or k) for k in latest_mapper_val.args]
            if latest_mapper_val.args
            else [previous_mapper.get(key)]
        )
        if for_serialization and previous_mapper.get(key) != key:
            raise NotImplementedError(
                "Combining functions and other mapping in a serialization mapper is unsupported"
            )
        return FunctionCall(func=latest_mapper_val.func, args=args)
    return latest_mapper.get(val, val)


def add_mapper_to_aggregation(latest_mapper, previous_mapper, for_serialization=False):
    result_mapper = {}  # copy.deepcopy(previous_mapper)
    if not isinstance(latest_mapper, (Mapping, mappers)):
        raise TypeError("Mapper must be a mapping")
    for k, v in previous_mapper.items():
        if v is DoNotSerialize:
            result_mapper[k] = DoNotSerialize
        elif isinstance(v, str):
            result_mapper[k] = _apply_mapper(
                latest_mapper, k, previous_mapper, for_serialization=for_serialization
            )
        elif isinstance(v, dict):
            if not k.endswith("._mapper"):
                raise ValueError(
                    "Invalid mapper. To map nested values, use the format <key>._mapper: {...}"
                )
            field_name = k[0:-8]
            mapped_key = (
                field_name
                if for_serialization
                else _apply_mapper(
                    latest_mapper,
                    field_name,
                    previous_mapper,
                    for_serialization,
                    is_self=True,
                )
            )

            sub_mapper = (
                latest_mapper.get(
                    f"{mapped_key}._mapper", latest_mapper.get(f"{field_name}._mapper")
                )
                if not isinstance(latest_mapper, mappers)
                else latest_mapper
            )
            if sub_mapper:
                result_mapper[f"{mapped_key}._mapper"] = add_mapper_to_aggregation(
                    sub_mapper, v, for_serialization=for_serialization
                )
            else:
                result_mapper[f"{mapped_key}._mapper"] = v
        elif isinstance(v, FunctionCall):
            args = v.args or [k]
            mapped_args = (
                args
                if for_serialization
                else [
                    _apply_mapper(
                        latest_mapper,
                        a,
                        previous_mapper,
                        for_serialization=for_serialization,
                        is_self=(a == k),
                    )
                    for a in args
                ]
            )
            if isinstance(latest_mapper, Mapping) and isinstance(
                latest_mapper.get(k), FunctionCall
            ):
                raise NotImplementedError(
                    "Combining multiple functions in serialization is unsupported"
                )
            result_mapper[k] = FunctionCall(func=v.func, args=mapped_args)

    return result_mapper


class DoNotSerialize:
    pass


class mappers(Enum):
    """Useful custom mappers"""

    TO_LOWERCASE = auto()
    TO_CAMELCASE = auto()
    NO_MAPPER = auto()


def get_mapper(val: Structure):
    return getattr(val.__class__, SERIALIZATION_MAPPER, {})


def aggregate_deserialization_mappers(
    cls, override_mapper=None, camel_case_convert=False
):
    base_mapper = _set_base_mapper_no_op(cls, for_serialization=False)
    aggregate_mapper = base_mapper
    override_mapper = (
        override_mapper
        if isinstance(override_mapper, list)
        else [override_mapper]
        if override_mapper
        else None
    )
    mappers_list = (
        override_mapper
        if override_mapper
        else cls.get_aggregated_deserialization_mapper()
    )
    for m in mappers_list:
        aggregate_mapper = add_mapper_to_aggregation(m, aggregate_mapper)
    if camel_case_convert:
        aggregate_mapper = add_mapper_to_aggregation(
            mappers.TO_CAMELCASE, aggregate_mapper
        )
    return aggregate_mapper


def aggregate_serialization_mappers(
    cls, override_mapper=None, camel_case_convert=False
):
    base_mapper = _set_base_mapper_no_op(cls, for_serialization=True)
    aggregate_mapper = base_mapper
    override_mapper = (
        override_mapper
        if isinstance(override_mapper, list)
        else [override_mapper]
        if override_mapper
        else None
    )
    mappers_list = (
        override_mapper
        if override_mapper
        else cls.get_aggregated_serialization_mapper()
    )
    for m in mappers_list:
        aggregate_mapper = add_mapper_to_aggregation(m, aggregate_mapper, True)
    if camel_case_convert:
        aggregate_mapper = add_mapper_to_aggregation(
            mappers.TO_CAMELCASE, aggregate_mapper, True
        )
    return aggregate_mapper

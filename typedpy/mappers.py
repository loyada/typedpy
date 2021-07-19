import copy
from enum import Enum, auto
from functools import reduce

from .structures import ClassReference, Structure
from .fields import FunctionCall

from typedpy.structures import MAPPER


def _deep_get(dictionary, deep_key):
    keys = deep_key.split(".")
    return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)


def _set_base_mapper_no_op(cls):
    mapper = {}
    for k, f in cls.get_all_fields_by_name().items():
        if isinstance(f, ClassReference):
            mapper[f"{k}._mapper"] = aggregate_mappers(f._ty)
        mapper[k] = k

    return mapper


def _convert_to_camelcase(key):
    words = key.split("_")
    return words[0] + "".join(w.title() for w in words[1:])


def _apply_mapper(latest_mapper, key, previous_mapper):
    val = previous_mapper[key]
    if latest_mapper == mappers.TO_CAMELCASE:
        return _convert_to_camelcase(val)
    if latest_mapper == mappers.TO_LOWERCASE:
        return val.upper()
    latest_mapper_val = latest_mapper.get(val, val)
    if isinstance(latest_mapper_val, (FunctionCall,)):
        args = (
            [_deep_get(previous_mapper, k) for k in latest_mapper_val.args]
            if latest_mapper_val.args
            else [previous_mapper.get(key)]
        )
        return FunctionCall(func=latest_mapper_val.func, args=args)
    return latest_mapper.get(val, val)


def add_mapper_to_aggregation(latest_mapper, previous_mapper):
    result_mapper = {}  # copy.deepcopy(previous_mapper)
    for k, v in previous_mapper.items():
        if isinstance(v, str):
            result_mapper[k] = _apply_mapper(latest_mapper, k, previous_mapper)
        elif isinstance(v, dict):
            if not k.endswith("._mapper"):
                raise ValueError("Invalid mapper. To map nested values, use the format <key>._mapper: {...}")
            field_name = k[0: -8]

            sub_mapper = (latest_mapper.get(f"{previous_mapper[field_name]}._mapper")
                          if not isinstance(latest_mapper, mappers)
                          else latest_mapper
                          )
            if sub_mapper:
                result_mapper[f"{previous_mapper[field_name]}._mapper"] = (
                    add_mapper_to_aggregation(sub_mapper, v)
                )
            else:
                result_mapper[f"{previous_mapper[field_name]}._mapper"] = v
        elif isinstance(v, FunctionCall):
            args = v.args or [k]
            mapped_args = [previous_mapper[a] for a in args]
            result_mapper[k] = FunctionCall(func=v.func, args=mapped_args)

    return result_mapper


class mappers(Enum):
    TO_LOWERCASE = auto()
    TO_CAMELCASE = auto()


def get_mapper(val: Structure):
    return getattr(val.__class__, MAPPER, {})


def aggregate_mappers(cls):
    base_mapper = _set_base_mapper_no_op(cls)
    aggregate_mapper = base_mapper
    for m in cls.get_aggregated_serialization_mapper():
        aggregate_mapper = add_mapper_to_aggregation(m, aggregate_mapper)

    return aggregate_mapper

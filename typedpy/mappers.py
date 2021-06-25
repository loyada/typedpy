from enum import Enum, auto

from typedpy import ClassReference, Structure
from typedpy.structures import MAPPER


def _get_to_lowercase(cls):
    mapper = {}
    for k, f in cls.get_all_fields_by_name().items():
        if isinstance(f, ClassReference):
            mapper[f"{k}._mapper"] = _get_to_lowercase(f._ty)
        mapper[k] = k.upper()

    return mapper


class mappers(Enum):
    TO_LOWERCASE = auto()
    TO_CAMELCASE = auto()


def get_mapper(val: Structure):
    return getattr(val.__class__, MAPPER, {})


def build_mapper(cls):
    mapper = getattr(cls, MAPPER, {})
    if mapper == mappers.TO_LOWERCASE:
        return _get_to_lowercase(cls)
    return {} if mapper == mappers.TO_CAMELCASE else mapper

from enum import Enum, auto

from typedpy import ClassReference, Structure
from typedpy.structures import MAPPER


def _get_to_lowercase(cls: type[Structure]):
    mapper = {}
    for k, f in cls.get_all_fields_by_name().items():
        if isinstance(f, ClassReference):
            mapper[f"{k}._mapper"] = _get_to_lowercase(f._ty)
        mapper[k] = k.upper()

    return mapper


class mappers(Enum):
    TO_LOWERCASE = auto()


def build_mapper(cls):
    mapper = getattr(cls, MAPPER, {})
    if not mapper:
        return {}
    return _get_to_lowercase(cls)

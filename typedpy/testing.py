import json
from typing import Set, Union

from typedpy import (
    AnyOf,
    Array,
    Boolean,
    ClassReference,
    Enum,
    Float,
    Integer,
    NoneField,
    Number,
    SerializableField,
    String,
    mappers,
)
from typedpy.commons import wrap_val
from typedpy.structures import Structure
from typedpy.structures.consts import DESERIALIZATION_MAPPER, SERIALIZATION_MAPPER

MISSING_VALUES = "missing values"
ADDITIONAL_VALUES = "additional values"
DIFFERENT_ORDER = "different location"


def _add_val(container: dict, key: str, diff):
    if key in container:
        container[key].append(diff)
    else:
        container[key] = [diff]


def _diff_set(val, otherval) -> dict:
    result = {}
    for v in val:
        if v not in otherval:
            _add_val(result, MISSING_VALUES, v)
    for v in otherval:
        if v not in val:
            _add_val(result, ADDITIONAL_VALUES, v)
    return result


def _diff_dict(val, otherval) -> dict:
    result = {}
    for key, v in val.items():
        if key not in otherval:
            _add_val(result, MISSING_VALUES, key)
        elif isinstance(v, Structure):
            diff = _find_diff(v, otherval[key])
            if diff:
                result[key] = diff
        elif isinstance(otherval[key], Structure):
            diff = _find_diff(otherval[key], v)
            if diff:
                result[key] = diff
        else:
            diff = _find_diff(otherval[key], v)
            if diff:
                result[key] = diff
    for key, v in otherval.items():
        if key not in val:
            _add_val(result, ADDITIONAL_VALUES, key)
        elif isinstance(v, Structure):
            diff = _find_diff(val[key], v)
            if diff:
                result[key] = diff
        elif key not in result:
            diff = _find_diff(val[key], v)
            if diff:
                result[key] = diff
    return result


def _diff_list(val, otherval, outer_result: dict, outer_key: str) -> dict:
    def _find_missing_vals(i, v, _otherval):
        diff = _find_diff(v, _otherval[i])
        if diff:
            if outer_key:
                outer_result[f"{outer_key}[{i}]"] = diff
            else:
                result[i] = diff
        else:
            internal_diff = _find_diff(
                v, _otherval[i], outer_result=outer_result, out_key=outer_key
            )
            if internal_diff:
                if outer_key:
                    outer_result[f"{outer_key}[{i}]"] = internal_diff
                else:
                    result[i] = internal_diff

    result = {}
    for i, v in enumerate(val):
        if len(otherval)>i and  v == otherval[i]:
            continue
        try:
            index = otherval.index(v)
            msg = f"index {i} vs {index}"
            _add_val(result, DIFFERENT_ORDER, msg)
        except ValueError:
            _find_missing_vals(i, v, _otherval=otherval)
    for i, v in enumerate(otherval):
        if v == val[i]:
            continue
        try:
            val.index(v)
            continue
        except ValueError:
            if outer_key and f"{outer_key}[{i}]" in outer_result or i in result:
                continue
            _find_missing_vals(i, v, _otherval=val)

    return result


def find_diff(first, second) -> Union[dict, str]:
    """
    Utility for testing to find the differences between two values that are "supposed"
    to be equal. This is useful to have more useful assertion error messages,
    especially with pytest, using pytest_assertrepr_compare.

    Arguments:
        first:
            first value. Can be a Structure, list, dict, set
        second:
            second value. Can be a Structure, list, dict, set

    Returns:
        a dictionary with the differences, or the difference is trivial - a string.
        Note that this function does not employ any sophisticated algorithm and is meant
        just as a best-effort utility for testing.

    Example of the output (taken from the unit tests):

    .. code-block:: python

        actual = find_diff(bar2, bar1)
        assert actual == {
            "f": {
                "m['aaa']": {"age": "123 vs 12"},
                "missing values": ["bbb"],
                "additional values": ["ccc"],
            },
            "missing values": ["x"],
        }

    """
    return _find_diff(first, second)


def _find_diff_collection(struct, other, outer_result, out_key):
    if isinstance(struct, (list, tuple)):
        if len(struct) != len(other):
            return f"length of {len(struct)} vs {len(other)}"
        res_val = _diff_list(
            struct, other, outer_result=outer_result, outer_key=out_key
        )
        if res_val and out_key:
            outer_result[out_key] = res_val
        return res_val
    elif isinstance(struct, dict):
        res_val = _diff_dict(struct, other)
        if res_val and outer_result:
            for i, vv in res_val.items():
                if i not in {MISSING_VALUES, ADDITIONAL_VALUES}:
                    outer_result[f"{out_key}[{wrap_val(i)}]"] = vv
                else:
                    outer_result[i] = vv
        return res_val
    else:  # is a set
        res_val = _diff_set(struct, other)
        if res_val and out_key:
            outer_result[out_key] = res_val
        return res_val


def _find_diff(
    struct, other, outer_result=None, out_key=None
) -> Union[dict, str]:  # pylint: disable=too-many-branches, too-many-statements
    if struct.__class__ != other.__class__:
        return {"class": f"{struct.__class__} vs. {other.__class__}"}
    if isinstance(struct, (list, tuple, set, dict)):
        return _find_diff_collection(
            struct, other, outer_result=outer_result, out_key=out_key
        )

    internal_props = ["_instantiated", "_trust_supplied_values"]
    res = {}
    if isinstance(struct, Structure):  # pylint: disable=too-many-nested-blocks
        _diff_structure_internal(internal_props, other, res, struct)
        for k in sorted(other.__dict__):
            if k in other.get_all_fields_by_name() and getattr(struct, k) == getattr(
                other, k
            ):
                continue
            if k not in internal_props:
                if k not in struct.__dict__:
                    _add_val(res, ADDITIONAL_VALUES, k)
    else:
        if struct != other:
            return f"{struct} vs {other}"

    return res


def _diff_structure_internal(internal_props, other, res, struct):
    for k, val in sorted(struct.__dict__.items()):
        if k not in internal_props:
            if k in struct.get_all_fields_by_name() and getattr(struct, k) == getattr(
                other, k
            ):
                continue
            if k not in other.__dict__:
                _add_val(res, MISSING_VALUES, k)
            elif val != other.__dict__.get(k):
                otherval = other.__dict__.get(k)
                if isinstance(val, Structure):
                    res[k] = _find_diff(val, otherval)
                elif isinstance(val, (list, tuple, set, dict)):
                    _diff_collecation_val_internal(k, otherval, res, val)

                else:
                    res[k] = _find_diff(val, otherval)


def _diff_collecation_val_internal(k, otherval, res, val):
    if val.__class__ != otherval.__class__:
        res[k] = {"class": f"{val.__class__} vs. {otherval.__class__}"}
    elif len(val) != len(otherval):
        res[k] = f"length of {len(val)} vs {len(otherval)}"
    else:
        if isinstance(val, (list, tuple)):
            res_val = _diff_list(val, otherval, outer_result=res, outer_key=k)
            if res_val:
                res[k] = res_val
        elif isinstance(val, dict):
            res_val = _diff_dict(val, otherval)
            if res_val:
                for i, vv in res_val.items():
                    if i not in {MISSING_VALUES, ADDITIONAL_VALUES}:
                        res[f"{k}[{wrap_val(i)}]"] = vv
                    else:
                        res[i] = vv
        elif isinstance(val, set):
            res_val = _diff_set(val, otherval)
            if res_val:
                res[k] = res_val


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, Structure) and isinstance(right, Structure) and op == "==":
        res = [
            "found the following differences between the structures:",
            json.dumps(_find_diff(left, right)),
        ]
        return res
    return None


def _assert_mapper_safe_for_trusted_deserialization(cls, wrapping_mapper=None):
    mapper = getattr(
        cls, DESERIALIZATION_MAPPER, getattr(cls, SERIALIZATION_MAPPER, {})
    )
    cls_name = cls.__name__
    if not mapper:
        if wrapping_mapper in [
            mappers.NO_MAPPER,
            mappers.TO_CAMELCASE,
            mappers.TO_LOWERCASE,
        ]:
            raise AssertionError(
                f"{cls_name} has no deserialization mapper, and its wrapping class has mapper: {wrapping_mapper}."
                "To guarantee trusted deserialization works consistently with serialization and non-trusted"
                f" deserialization, add the same mapper to {cls_name}"
            )
    if wrapping_mapper in [
        mappers.NO_MAPPER,
        mappers.TO_CAMELCASE,
        mappers.TO_LOWERCASE,
    ]:
        if mapper is not wrapping_mapper:
            raise AssertionError(
                f"{cls_name} has mapper {mapper}, and its wrapping class has one: {wrapping_mapper}."
                "To guarantee trusted deserialization works consistently with serialization and non-trusted"
                f" deserialization, add the same mapper to {cls_name}"
            )
    if mapper in [mappers.NO_MAPPER, mappers.TO_CAMELCASE, mappers.TO_LOWERCASE]:
        return
    if not isinstance(mapper, dict):
        raise AssertionError(
            f"{cls_name} has a custom mapper {mapper}. For custom mappers, nly simple dicts are supported for trusted deserialization."
        )
    for k, v in mapper.items():
        if k.endswith("._mapper"):
            raise AssertionError(
                f"{cls_name} has a custom mapper with an unsupported direct nested mapping for {k}. No direct nested mapping are supported"
            )

        if not isinstance(v, str):
            raise AssertionError(
                f"{cls_name} has a custom mapper with an unsupported mapping value for {k}. Only key name mappings are supported."
            )
    return


_valid_classes_for_trusted_deserialization = (
    Integer,
    String,
    Float,
    Boolean,
    NoneField,
    Enum,
    SerializableField,
    Number,
)


def _is_optional_anyof(field: AnyOf) -> bool:
    return len(field.get_fields()) == 2 and NoneField in [
        x.__class__ for x in field.get_fields()
    ]


def assert_trusted_deserialization_mapper_is_safe(cls, wrapping_mapper=None):
    _assert_mapper_safe_for_trusted_deserialization(
        cls, wrapping_mapper=wrapping_mapper
    )

    mapper = getattr(
        cls, DESERIALIZATION_MAPPER, getattr(cls, SERIALIZATION_MAPPER, {})
    )
    for v in cls.get_all_fields_by_name().values():
        if isinstance(v, _valid_classes_for_trusted_deserialization):
            continue
        if isinstance(v, AnyOf):
            if _is_optional_anyof(v):
                continue
            for f in v.get_fields():
                if not isinstance(f, _valid_classes_for_trusted_deserialization):
                    raise AssertionError(
                        f"{cls.__name__} as a field of type {f}, which is unsupported"
                    )
            continue
        if isinstance(v, Array):
            if isinstance(v.items, _valid_classes_for_trusted_deserialization):
                continue
            if isinstance(
                v.items, ClassReference
            ) and assert_trusted_deserialization_mapper_is_safe(
                v.items.get_type,
                wrapping_mapper=mapper,
            ):
                continue
        if isinstance(v, Set):
            if isinstance(v.items, _valid_classes_for_trusted_deserialization):
                continue
            if isinstance(
                v.items, ClassReference
            ) and assert_trusted_deserialization_mapper_is_safe(
                v.items.get_type,
                wrapping_mapper=mapper,
            ):
                continue
        if isinstance(
            v, ClassReference
        ) and assert_trusted_deserialization_mapper_is_safe(
            v.get_type, wrapping_mapper=mapper
        ):
            continue

    return

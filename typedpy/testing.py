import json
from typing import Union

from .commons import wrap_val
from .structures import Structure

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
            result[key] = f"{v} vs {otherval[key]}"
    for key, v in otherval.items():
        if key not in val:
            _add_val(result, ADDITIONAL_VALUES, key)
        elif isinstance(v, Structure):
            diff = _find_diff(val[key], v)
            if diff:
                result[key] = diff
        else:
            result[key] = f"{v} vs {otherval[key]}"
    return result


def _diff_list(
    val, otherval, outer_result: dict, outer_key: str
) -> dict:  # pylint: disable=too-many-branches
    result = {}
    for i, v in enumerate(val):
        if v == otherval[i]:
            continue
        try:
            index = otherval.index(v)
            msg = f"index {i} vs {index}"
            _add_val(result, DIFFERENT_ORDER, msg)
        except ValueError:
            diff = _find_diff(v, otherval[i])
            if diff:
                if outer_key:
                    outer_result[f"{outer_key}[{i}]"] = diff
                else:
                    result[i] = diff
            else:
                internal_diff = _find_diff(
                    v, otherval[i], outer_result=outer_result, out_key=outer_key
                )
                if internal_diff:
                    if outer_key:
                        outer_result[f"{outer_key}[{i}]"] = internal_diff
                    else:
                        result[i] = internal_diff
    for i, v in enumerate(otherval):
        if v == val[i]:
            continue
        try:
            val.index(v)
            continue
        except ValueError:
            if outer_key and f"{outer_key}[{i}]" in outer_result or i in result:
                continue
            diff = _find_diff(v, val[i])
            if diff:
                if outer_key:
                    outer_result[f"{outer_key}[{i}]"] = diff
                else:
                    result[i] = diff
            else:
                internal_diff = _find_diff(
                    v, otherval[i], outer_result=outer_result, out_key=outer_key
                )
                if internal_diff:
                    if outer_key:
                        outer_result[f"{outer_key}[{i}]"] = internal_diff
                    else:
                        result[i] = internal_diff
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


def _find_diff(struct, other, outer_result=None, out_key=None) -> Union[dict, str]:

    if struct.__class__ != other.__class__:
        return {"class": f"{struct.__class__} vs. {other.__class__}"}
    if isinstance(struct, (list, tuple)):
        res_val = _diff_list(
            struct, other, outer_result=outer_result, outer_key=out_key
        )
        if res_val and out_key:
            outer_result[out_key] = res_val
        return res_val
    elif isinstance(struct, dict):
        res_val = _diff_dict(struct, other)
        if res_val and outer_result:
            for i in res_val:
                if i not in {MISSING_VALUES, ADDITIONAL_VALUES}:
                    outer_result[f"{out_key}[{wrap_val(i)}]"] = res_val[i]
                else:
                    outer_result[i] = res_val[i]
        return res_val
    elif isinstance(struct, set):
        res_val = _diff_set(struct, other)
        if res_val and out_key:
            outer_result[out_key] = res_val
        return res_val

    internal_props = ["_instantiated"]
    res = {}
    if isinstance(struct, Structure):  #  pylint: disable=too-many-nested-blocks
        for k, val in sorted(struct.__dict__.items()):
            if k not in internal_props:
                if k not in other.__dict__:
                    _add_val(res, MISSING_VALUES, k)
                elif val != other.__dict__.get(k):
                    otherval = other.__dict__.get(k)
                    if isinstance(val, Structure):
                        res[k] = _find_diff(val, otherval)
                    elif isinstance(val, (list, tuple, set, dict)):
                        if val.__class__ != otherval.__class__:
                            res[k] = {
                                "class": f"{val.__class__} vs. {otherval.__class__}"
                            }
                        elif len(val) != len(otherval):
                            res[k] = f"length of {len(val)} vs {len(otherval)}"
                        else:
                            if isinstance(val, (list, tuple)):
                                res_val = _diff_list(
                                    val, otherval, outer_result=res, outer_key=k
                                )
                                if res_val:
                                    res[k] = res_val
                            elif isinstance(val, dict):
                                res_val = _diff_dict(val, otherval)
                                if res_val:
                                    for i in res_val:
                                        if i not in {MISSING_VALUES, ADDITIONAL_VALUES}:
                                            res[f"{k}[{wrap_val(i)}]"] = res_val[i]
                                        else:
                                            # _add_val(res, ADDITIONAL_VALUES, k)
                                            res[i] = res_val[i]
                            elif isinstance(val, set):
                                res_val = _diff_set(val, otherval)
                                if res_val:
                                    res[k] = res_val

                    else:
                        res[k] = _find_diff(val, otherval)
        for k, val in sorted(other.__dict__.items()):
            if k not in internal_props:
                if k not in struct.__dict__:
                    _add_val(res, ADDITIONAL_VALUES, k)
    else:
        if struct != other:
            return f"{struct} vs {other}"

    return res


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, Structure) and isinstance(right, Structure) and op == "==":
        res = [
            "found the following differences between the structures:",
            json.dumps(_find_diff(left, right)),
        ]
        return res

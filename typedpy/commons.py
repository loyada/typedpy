import json
import sys
from functools import reduce


def wrap_val(v):
    return f"'{v}'" if isinstance(v, str) else v


def _is_dunder(name):
    """Returns True if a __dunder__ name, False otherwise."""
    return (
        len(name) > 4
        and name[:2] == name[-2:] == "__"
        and name[2] != "_"
        and name[-3] != "_"
    )


def _is_sunder(name):
    """Returns True if a _sunder name, False otherwise."""
    return len(name) > 2 and name[0] == "_" and name[1:2] != "_"


def raise_errs_if_needed(errors):
    if errors:
        messages = json.dumps([str(e) for e in errors])
        raise errors[0].__class__(messages) from errors[0]


def deep_get(dictionary, deep_key):
    keys = deep_key.split(".")
    return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)


def first_in(iterable):
    return next(iter(iterable), None)


def nested(func, default=None):
    try:
        return func()
    except (AttributeError, IndexError):
        return default


py_version = sys.version_info[0:2]
python_ver_36 = py_version == (3, 6)
python_ver_atleast_than_37 = py_version > (3, 6)
python_ver_atleast_39 = py_version >= (3, 9)

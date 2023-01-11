import json
import sys
import builtins

from collections.abc import Iterable, Mapping, Generator
from functools import reduce, wraps
from inspect import signature
from typing import Optional, Union

py_version = sys.version_info[0:2]
python_ver_36 = py_version == (3, 6)
python_ver_atleast_than_37 = py_version > (3, 6)
python_ver_atleast_39 = py_version >= (3, 9)
python_ver_atleast_310 = py_version >= (3, 10)

INDENT = " " * 4

builtins_types = [
    getattr(builtins, k)
    for k in dir(builtins)
    if isinstance(getattr(builtins, k), type)
]


class UndefinedMeta(type):
    def __bool__(cls):
        return False


class Undefined(metaclass=UndefinedMeta):
    pass


def wrap_val(v):
    return f"'{v}'" if isinstance(v, str) else v


def doublewrap_val(v):
    return f'"{v}"' if isinstance(v, str) else v


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


class InvalidStructureErr(ValueError, TypeError):
    pass


def raise_errs_if_needed(cls, errors):
    if errors:
        cls_name = cls.__name__
        messages = [f"{cls_name}.{e}" for e in errors]
        raise InvalidStructureErr(json.dumps(messages)) from errors[0]


def first_in(my_list: Iterable, ignore_none: bool = False) -> Optional:
    """
    get the first in an Iterable (i.e. list, tuple, generator, dict, etc.).
    Optionally ignoring None values.

       Arguments:
           my_list(Iterable):
               The input iterable, such as a list
           ignore_none(bool): optional
               whether or not to ignore None values. Default is False


       Returns:
           The first value found in the input, or None if none found
    """
    if ignore_none:
        return next(filter(None, iter(my_list)), None)
    return next(iter(my_list), None)


def nested(func, default=None):
    """
    get a nested value if it exists, or return the given default if it doesn't

        Arguments:
            func(function):
                A function with no arguments that returns the nested value
            default:
                the default value, in case the nested value does not exist


        Returns:
            the nested attribute(s) or the default value. For example:

        For example:

            .. code-block:: python

               d = D(c=C(b=B(a=A(i=5))))
               assert nested(lambda: d.c.b.a.i) == 5

               d.c.foo = [1, 2, 3]
               assert nested(lambda: d.c.foo[100]) is None
               assert nested(lambda: d.c.foo[2]) == 3
    """
    try:
        return func()
    except (AttributeError, TypeError, IndexError, KeyError):
        return default


def flatten(iterable, ignore_none=False) -> list:
    """
    Flatten an iterable completely, getting rid of None values

       Arguments:
              iterable(Iterable):
                   the input
              ignore_none(bool): optional
                   whether to skip None values or not. Default is False.

       Returns:
           A flattened list

           .. code-block:: python

              flatten(
              [
                [[1]],
                [[2], 3, None, (5,)],
                []
              ], ignore_none=True) == [1, 2, 3, 5]

    """
    res = (
        sum([flatten(x, ignore_none) for x in iterable], [])
        if isinstance(iterable, (list, tuple, Generator))
        else [iterable]
    )
    if isinstance(res, (list, tuple, Generator)) and ignore_none:
        return [x for x in res if x is not None]
    return res


def deep_get(
    dictionary, deep_key, default=None, do_flatten=False, *, enable_undefined=False
):
    """
    Get a nested value from within a dictionary. Supports also nested lists, in
    which case the result is a a list of values

    Arguments:
           dictionary(dict):
                the input
           deep_key(str):
                nested key of the form aaa.bbb.ccc.ddd
           default:
                the default value, in case the path does not exist
           do_flatten(bool): optional
                flatten the outputs, in case the result is multiple outputs
           enable_undefined(bool): optional
                if set, then keys that are not in the dictionary return Undefined.
                otherwise, returns None for undefined keys. Default is False.

    Returns:
        the nested attribute(s) or the default value. For example:

    For example:

        .. code-block:: python

           example = {"a": {"b": [{"c": [None, {"d": [1]}]}, {"c": [None, {"d": [2]}, {"d": 3}]}, {"c": []}]}}
           assert deep_get(example, "a.b.c.d") == [[[1]], [[2], 3], []]
           assert deep_get(example, "a.b.c.d", do_flatten=True) == [1, 2, 3]

    """

    def _get_next_level(
        d: Optional[Union[Mapping, Iterable]], key, default, *, enable_undefined
    ):
        if isinstance(d, Mapping):
            if enable_undefined and key not in d:
                return Undefined
            return d.get(key, default)
        if isinstance(d, (list, tuple, Generator)):
            res = [
                _get_next_level(r, key, default, enable_undefined=enable_undefined)
                for r in d
                if r is not None
            ]
            return res
        return default

    keys = deep_key.split(".")
    result = reduce(
        lambda d, key: _get_next_level(
            d, key, default, enable_undefined=enable_undefined
        )
        if d
        else default,
        keys,
        dictionary,
    )
    if isinstance(result, (list, tuple, Generator)) and do_flatten:
        result = flatten(result)
    return result


def default_factories(func):
    """
     A function decorator that allows to have default values that are generators of the actual
     default values to be used. This is useful when the default values are mutable, like
     dicts or lists

        Arguments:
               iterable(Iterable):
                    the input
               ignore_none(bool): optional
                    whether to skip None values or not. Default is False.

        Returns:
            A flattened list

    For example:

            .. code-block:: python

               @default_factories
               def func(a, b = 0, c = list, d = dict):
                    return a, b, c, d

               assert func(1) == 1, 0, [] , {}

    """
    func_signature = signature(func, follow_wrapped=True)

    @wraps(func)
    def decorated(*args, **kwargs):
        bound = func_signature.bind(*args, **kwargs)

        for k, v in func_signature.parameters.items():
            if k not in bound.arguments:
                default = (
                    v.default()
                    if callable(v.default) and v.default != v.empty
                    else v.default
                )
                if v.default != v.empty:
                    kwargs[k] = default
        return func(*args, **kwargs)

    return decorated


class Constant:
    """
    Mark a value as constant in a mapper.
    This is useful if an attribute did not exist in a previous version
    and you want to assign it to a default value in the more recent version.
    """

    def __init__(self, val):
        self._val = val

    def __call__(self, *args, **kwargs):
        return self._val

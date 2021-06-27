import typing
from collections import deque

from .commons import python_ver_36, python_ver_atleast_39, python_ver_atleast_than_37


def type_is_generic(v):
    """
    Return whether or not the given type is a "standard generic",
    such as list[int], List[int], dict[int, str]
    :param v: the type
    :return: True if it is a generic, False otherwise
    """

    class Foo:
        pass

    origin = getattr(v, "__origin__", None)
    typing_base = getattr(typing, "_TypingBase", Foo)
    generic_alias = getattr(typing, "_GenericAlias", Foo)
    special_generic_alias = getattr(typing, "_SpecialGenericAlias", Foo)
    return (
        (python_ver_36 and isinstance(v, typing_base))
        or (
            python_ver_atleast_than_37
            and isinstance(v, (generic_alias, special_generic_alias))
        )
        or (
            python_ver_atleast_39
            and origin in {list, dict, tuple, set, frozenset, deque, typing.Union}
        )
    )


def get_list_type(the_type):
    """
    If the_type is a generic list type (e.g. list[int]), returns a Tuple
    of (list, <the internal type>). otherwise throws a TypeError
    :param the_type: a type that is supposed to be a "generic list", such as list[str]
    :return: a tuple of (list, <the internal type>)
    """
    if type_is_generic(the_type):
        origin = getattr(the_type, "__origin__", None)
        if origin == list:
            args = getattr(the_type, "__args__", [None])
            if len(args) == 1:
                return list, args[0]
    raise TypeError("not a list of a single type")


def maybe(func, default_val=None):
    try:
        return func()
    except AttributeError:
        return default_val

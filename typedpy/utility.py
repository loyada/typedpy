import typing
from collections import deque
from pathlib import Path


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
    generic_alias = getattr(typing, "_GenericAlias", Foo)
    special_generic_alias = getattr(typing, "_SpecialGenericAlias", Foo)
    generic_origins = {list, dict, tuple, set, frozenset, deque, typing.Union}
    return isinstance(v, (generic_alias, special_generic_alias)) or (
        origin in generic_origins
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


def get_abs_path_from_here(relative_path: str, calling_file_name: str) -> Path:
    """
    return absolute path to file, based on path from the calling location
    :param calling_file_name: optional name of the calling script that will serce as reference
    :param relative_path: relative path from the loading source file
    :return: absolute path with resolved symlinks
    """
    calling_source_file = calling_file_name
    full_path: Path = Path(calling_source_file).parent / relative_path
    return full_path.resolve()

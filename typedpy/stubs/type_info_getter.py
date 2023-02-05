import collections.abc
import logging
import typing

from typedpy.commons import builtins_types
from typedpy.fields import AllOf, AnyOf, Map, OneOf, Enum
from typedpy.structures import Field, NoneField
from typedpy.structures.structures import get_typing_lib_info
from typedpy.utility import type_is_generic


def _get_anyof_typing(field, locals_attrs, additional_classes):
    union_fields = getattr(field, "_fields", [])
    if len(union_fields) == 2 and isinstance(union_fields[1], NoneField):
        info = get_type_info(union_fields[0], locals_attrs, additional_classes)
        return f"Optional[{info}] = None"

    fields = ",".join(
        [get_type_info(f, locals_attrs, additional_classes) for f in union_fields]
    )
    return f"Union[{fields}]"


def is_typeddict(the_type):
    return the_type.__class__.__name__ == "_TypedDictMeta"


def _get_type_info_for_typing_generic(
    the_type, locals_attrs, additional_classes
) -> typing.Optional[str]:
    origin = getattr(the_type, "__origin__", None)
    args = getattr(the_type, "__args__", [])
    if origin in {list, set, tuple}:
        return _get_type_info_from_single_type_collection(
            additional_classes, args, locals_attrs, origin
        )
    mapped_args = (
        [get_type_info(a, locals_attrs, additional_classes) for a in args]
        if args
        else []
    )

    if origin is collections.abc.Callable:
        args_st = (
            ""
            if not mapped_args
            else f"[{mapped_args[0]}]"
            if len(mapped_args) == 1
            else f"[[{','.join(mapped_args[:-1])}], {mapped_args[-1]}]"
        )
        additional_classes.add(typing.Callable)
        return f"Callable{args_st}"
    if origin is dict:
        if mapped_args:
            return f"dict[{', '.join(mapped_args)}]"
        return "dict"
    if origin is collections.abc.Iterable:
        additional_classes.add(typing.Iterable)
        args_st = "" if not mapped_args else f"[{mapped_args[0]}]"
        return f"Iterable{args_st}"

    if origin is collections.abc.Mapping:
        additional_classes.add(typing.Mapping)
        args_st = "" if not mapped_args else f"[{', '.join(mapped_args)}]"
        return f"Mapping{args_st}"

    if origin is type:
        args_st = "" if not mapped_args else f"[{', '.join(mapped_args)}]"
        return f"Type{args_st}"

    if origin is collections.abc.Iterator:
        additional_classes.add(typing.Iterator)
        args_st = "" if not mapped_args else f"[{mapped_args[0]}]"
        return f"Iterator{args_st}"

    if origin is typing.Union:
        if "None" in mapped_args:
            mapped_args = [a for a in mapped_args if str(a) != "None"]
            the_type = "Optional"
        else:
            the_type = "Type"
        args_st = "" if not mapped_args else f"[{', '.join(mapped_args)}]"
        return f"{the_type}{args_st}"

    if origin and mapped_args:
        mapped_origin = get_type_info(origin, locals_attrs, additional_classes)
        args_st = "" if not mapped_args else f"[{', '.join(mapped_args)}]"
        return f"{mapped_origin}{args_st}"
    return None


def _get_type_info_from_single_type_collection(
    additional_classes, args, locals_attrs, origin
):
    if len(args) != 1:
        return origin.__name__
    return (
        f"{origin.__name__}[{get_type_info(args[0], locals_attrs, additional_classes)}]"
    )


def _found_in_local_attrs(field, attrs):
    for k, v in attrs.items():
        if v is field:
            return k
    return None


def _get_resolved_type_info(field, the_type, locals_attrs, additional_classes):
    if is_typeddict(the_type):
        the_type = dict

    if the_type in builtins_types:
        return the_type.__name__

    if the_type in [typing.Optional, typing.Union, typing.NoReturn]:
        return getattr(the_type, "_name")
    if the_type is typing.Any:
        return "Any"
    if (
        getattr(the_type, "__module__", None)
        and the_type.__module__ != "builtins"
        and the_type not in locals_attrs
        and not type_is_generic(the_type)
    ):
        additional_classes.add(field)

    if type_is_generic(the_type):
        res = _get_type_info_for_typing_generic(
            the_type, locals_attrs, additional_classes
        )
        if res:
            return res

        return get_type_info(
            get_typing_lib_info(field), locals_attrs, additional_classes
        )

    return the_type.__name__


def get_type_info(field, locals_attrs, additional_classes):
    try:
        if field is ...:
            return "..."
        found_import_key = _found_in_local_attrs(field, locals_attrs)
        if found_import_key:
            return found_import_key
        if isinstance(field, (list, dict)):
            cls_name = field.__class__.__name__
            mapped_args = [
                get_type_info(a, locals_attrs, additional_classes) for a in field
            ]
            args_st = "" if not mapped_args else f"[{', '.join(mapped_args)}]"
            return f"{cls_name}{args_st}"

        if field in [None, type(None)]:
            return "None"
        if isinstance(field, (AnyOf, OneOf, AllOf)):
            return _get_anyof_typing(field, locals_attrs, additional_classes)

        if isinstance(field, Map):
            if not field.items:
                return "dict"
            sub_types = ", ".join(
                [
                    get_type_info(f, locals_attrs, additional_classes)
                    for f in field.items
                ]
            )
            return f"dict[{sub_types}]"

        if isinstance(field, Enum) and field._is_enum:
            additional_classes.add(field._enum_class)
            return field._enum_class.__name__

        the_type = (
            getattr(field, "get_type", field) if isinstance(field, Field) else field
        )
        # deal with from __future__ import annotations. Using eval is not a proble given it is not in run time.
        if isinstance(the_type, str):
            the_type = eval(the_type, locals_attrs)  # pylint: disable=eval-used
            field = the_type
            if isinstance(the_type, str):
                return the_type

        return _get_resolved_type_info(
            field, the_type, locals_attrs, additional_classes
        )

    except Exception as e:
        logging.exception(e)
        return "Any"


def get_all_type_info(cls, locals_attrs, additional_classes) -> dict:
    type_by_name = {}
    constants = getattr(cls, "_constants", {})
    required = getattr(cls, "_required", None)
    for field_name, field in cls.get_all_fields_by_name().items():
        if field_name in constants:
            continue
        try:
            type_info_str: str = get_type_info(field, locals_attrs, additional_classes)
            if (
                field_name not in required
                and required is not None
                and not type_info_str.startswith("Optional[")
            ):
                type_info_str = f"Optional[{type_info_str}] = None"
            type_by_name[field_name] = type_info_str
        except Exception as e:
            logging.exception(e)

    return type_by_name

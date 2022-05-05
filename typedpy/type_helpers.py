import collections.abc
import enum
import importlib.util
import inspect
import logging
import os
import sys
import builtins
import typing
from os.path import relpath
from pathlib import Path
import ast

from .commons import wrap_val, nested
from .fields import AllOf, AnyOf, FunctionCall, Map, OneOf
from .enum import Enum
from .serialization_wrappers import Deserializer, Serializer
from .structures import (
    ImmutableStructure,
    NoneField,
    Structure,
    Field,
    get_typing_lib_info,
)
from .types_ast import get_imports, get_models, models_to_src
from .utility import type_is_generic

builtins_types = [
    getattr(builtins, k)
    for k in dir(builtins)
    if isinstance(getattr(builtins, k), type)
]

module = getattr(inspect, "__class__")

INDENT = " " * 4

AUTOGEN_NOTE = [
    "",
    "#### This stub was autogenerated by Typedpy",
    "###########################################",
    "",
]


_private_to_public_pkg = {"werkzeug.localxxx": "flask"}


def _get_package(v, attrs):
    pkg_name = attrs.get("__package__") or "%^$%^$%^#"
    if v.startswith(pkg_name):
        return v[len(pkg_name) :]
    return _private_to_public_pkg.get(v, v)


def _as_something(k, attrs):
    return f" as {k}" if attrs.get("__file__", "").endswith("__init__.py") else ""


def _get_anyof_typing(field, locals_attrs, additional_classes):
    union_fields = getattr(field, "_fields", [])
    if len(union_fields) == 2 and isinstance(union_fields[1], NoneField):
        info = _get_type_info(union_fields[0], locals_attrs, additional_classes)
        return f"Optional[{info}] = None"

    fields = ",".join(
        [_get_type_info(f, locals_attrs, additional_classes) for f in union_fields]
    )
    return f"Union[{fields}]"


def _get_type_info_for_typing_generic(
    the_type, locals_attrs, additional_classes
) -> typing.Optional[str]:
    origin = getattr(the_type, "__origin__", None)
    args = getattr(the_type, "__args__", [])
    if origin in {list, set, tuple}:
        if len(args) != 1:
            return origin.__name__
        return f"{origin.__name__}[{_get_type_info(args[0], locals_attrs, additional_classes)}]"
    mapped_args = (
        [_get_type_info(a, locals_attrs, additional_classes) for a in args]
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

    return None


def _found_in_local_attrs(field, attrs):
    for k, v in attrs.items():
        if v is field:
            return k
    return None


def _get_type_info(field, locals_attrs, additional_classes):
    try:
        if field is ...:
            return "..."
        found_import_key = _found_in_local_attrs(field, locals_attrs)
        if found_import_key:
            return found_import_key
        if isinstance(field, (list, dict)):
            cls_name = field.__class__.__name__
            mapped_args = [
                _get_type_info(a, locals_attrs, additional_classes) for a in field
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
                    _get_type_info(f, locals_attrs, additional_classes)
                    for f in field.items
                ]
            )
            return f"dict[{sub_types}]"

        if isinstance(field, Enum):
            if field._is_enum:
                additional_classes.add(field._enum_class)
                return field._enum_class.__name__

        the_type = (
            getattr(field, "get_type", field) if isinstance(field, Field) else field
        )
        # deal with from __future__ import annotations
        if isinstance(the_type, str):
            the_type = eval(the_type, locals_attrs)
            field = the_type
            if isinstance(the_type, str):
                return the_type

        if the_type in builtins_types:
            return the_type.__name__

        if the_type in [typing.Any, typing.Optional, typing.Union, typing.NoReturn]:
            return getattr(the_type, "_name")
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

            return _get_type_info(
                get_typing_lib_info(field), locals_attrs, additional_classes
            )

        return the_type.__name__
    except Exception as e:
        logging.exception(e)
        return "Any"


def _get_all_type_info(cls, locals_attrs, additional_classes) -> dict:
    type_by_name = {}
    required = getattr(cls, "_required", None)
    for field_name, field in cls.get_all_fields_by_name().items():
        try:
            type_info_str: str = _get_type_info(field, locals_attrs, additional_classes)
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


def _get_struct_classes(attrs, only_calling_module=True):
    return {
        k: v
        for k, v in attrs.items()
        if (
            inspect.isclass(v)
            and issubclass(v, Structure)
            and (v.__module__ == attrs["__name__"] or not only_calling_module)
            and v not in {Deserializer, Serializer, ImmutableStructure, FunctionCall}
        )
    }


def _get_imported_classes(attrs):
    def _valid_module(v):
        return hasattr(v, "__module__") and attrs["__name__"] != v.__module__

    res = []
    for k, v in attrs.items():
        if (
            not k.startswith("_")
            and (isinstance(v, module) or _valid_module(v))
            and not _is_internal_sqlalchemy(v)
        ):
            if isinstance(v, module):
                if v.__name__ != k:
                    parts = v.__name__.split(".")
                    if len(parts) > 1:
                        first_parts = parts[:-1]
                        last_part = parts[-1]
                        res.append(
                            (
                                k,
                                f"from {'.'.join(first_parts)} import {last_part} as {k}",
                            )
                        )
                    elif nested(lambda: getattr(v.os, k)) == v:
                        res.append((k, f"from os import {k} as {k}"))
                else:
                    res.append((k, f"import {k}"))
            else:
                pkg = _get_package(v.__module__, attrs)

                name_in_pkg = getattr(v, "__name__", k)
                name_to_import = name_in_pkg if name_in_pkg and name_in_pkg != k else k
                as_import = (
                    _as_something(k, attrs) if name_to_import == k else f" as {k}"
                )
                import_stmt = f"from {pkg} import {name_to_import}{as_import}"
                if pkg == "__future__":
                    res = [(k, import_stmt)] + res
                else:
                    res.append((k, import_stmt))
    return res


def _get_ordered_args(unordered_args: dict):
    optional_args = {k: v for k, v in unordered_args.items() if v.endswith("= None")}
    mandatory_args = {k: v for k, v in unordered_args.items() if k not in optional_args}
    return {**mandatory_args, **optional_args}


def _get_mapped_extra_imports(additional_imports) -> dict:
    mapped = {}
    for c in additional_imports:
        try:
            name = _get_type_info(c, {}, set())
            if inspect.isclass(c) and issubclass(c, Structure):
                module_name = c.__module__
            else:
                module_name = (
                    c.get_type.__module__
                    if isinstance(c, Field)
                    else c.__module__
                    if name != "Any"
                    else None
                )
            if module_name:
                mapped[name] = module_name
        except Exception as e:
            logging.exception(e)
    return mapped


def _is_sqlalchemy(attr):
    module_name = getattr(attr, "__module__", "")
    return module_name and (
        module_name.startswith("sqlalchemy.orm")
        or module_name.startswith("sqlalchemy.sql")
    )


def _is_internal_sqlalchemy(attr):
    module_name = getattr(attr, "__module__", "")
    return module_name in {"sqlalchemy.orm.decl_api", "sqlalchemy.sql.schema"}


def _try_extract_column_type(attr):
    if attr.__class__.__name__ == "InstrumentedAttribute":
        return next(iter(attr.expression.base_columns)).type.python_type


def _skip_sqlalchemy_attribute(attribute):
    return attribute.startswith("_") or attribute in {"registry", "metadata"}


def _get_method_and_attr_list(cls, members):
    all_fields = cls.get_all_fields_by_name() if issubclass(cls, Structure) else {}
    ignored_methods = (
        dir(Structure)
        if issubclass(cls, Structure)
        else dir(Field)
        if issubclass(cls, Structure)
        else dir(enum)
        if issubclass(cls, enum.Enum)
        else {}
    )
    private_prefix = "_" if issubclass(cls, enum.Enum) else "__"
    method_list = []
    attrs = []
    cls_dict = cls.__dict__
    for attribute in members:
        if attribute.startswith(private_prefix):
            continue
        attr = (
            cls_dict.get(attribute)
            if attribute in cls_dict
            else getattr(cls, attribute, None)
        )
        if _is_sqlalchemy(attr):
            if not _skip_sqlalchemy_attribute(attribute):
                members[attribute] = _try_extract_column_type(attr)
                attrs.append(attribute)
            continue
        is_func = not inspect.isclass(attr) and (
            callable(attr) or isinstance(attr, (property, classmethod, staticmethod))
        )
        if not any(
            [
                attr is None,
                inspect.isclass(attr),
                is_func,
                isinstance(attr, cls),
                issubclass(cls, Structure),
            ]
        ):
            attrs.append(attribute)
            continue

        if is_func and attribute not in all_fields and attribute not in ignored_methods:
            method_list.append(attribute)

    if (
        not issubclass(cls, Structure)
        and not issubclass(cls, enum.Enum)
        and "__init__" in members
    ):
        method_list = ["__init__"] + method_list

    for name in cls_dict.get("__annotations__", {}):
        if name not in attrs and not issubclass(cls, Structure):
            attrs.append(name)
    return method_list, attrs


def _is_sqlalchemy_orm_model(cls):
    return nested(lambda: str(cls.__class__.__module__), "").startswith(
        "sqlalchemy.orm"
    )


def _get_sqlalchemy_init(attributes_with_type):
    res = [f"def __init__(self, *,"]
    for p, p_type in attributes_with_type:
        res.append(f"{INDENT}{p}: {p_type} = None,")
    res.append(f"{INDENT}**kw")
    res.append(f"): ...")
    return res


def _get_methods_info(cls, locals_attrs, additional_classes) -> list:
    method_by_name = []
    members = {}
    members.update(dict(cls.__dict__))
    annotations = cls.__dict__.get("__annotations__", {})
    for a in annotations:
        members[a] = annotations[a]
    members.update(annotations)

    method_list, cls_attrs = _get_method_and_attr_list(cls, members)
    attributes_with_type = []
    for attr in cls_attrs:
        the_type = members.get(attr, None)
        if getattr(the_type, "__module__", "").startswith("_") or nested(
            lambda: the_type.__class__.__name__, ""
        ).startswith("_"):
            # private class/module
            continue
        if inspect.isclass(the_type) or type_is_generic(the_type):
            resolved_type = (
                _get_type_info(the_type, locals_attrs, additional_classes)
                if the_type
                else "Any"
            )
        else:
            resolved_type = (
                _get_type_info(the_type.__class__, locals_attrs, additional_classes)
                if the_type is not None
                else "Any"
            )
        attributes_with_type.append((attr, resolved_type))
    method_by_name = [
        f"{attr}: {resolved_type}" for (attr, resolved_type) in attributes_with_type
    ]
    cls_dict = cls.__dict__

    for name in method_list:
        method_cls = members[name].__class__
        is_property = False
        func = cls_dict.get(name) if name in cls_dict else getattr(cls, name, None)
        func = (
            getattr(cls, name)
            if isinstance(func, (classmethod, staticmethod, property))
            and not _is_sqlalchemy(func)
            else func
        )
        if isinstance(func, property):
            is_property = True
            func = func.__get__
        try:
            sig = inspect.signature(func)
            return_annotations = (
                ""
                if sig.return_annotation == inspect._empty
                else f" -> {_get_type_info(sig.return_annotation, locals_attrs, additional_classes)}"
            )
            params_by_name = []
            if _is_sqlalchemy_orm_model(cls) and name == "__init__":
                method_by_name.extend(_get_sqlalchemy_init(attributes_with_type))
                continue

            if method_cls is classmethod:
                params_by_name.append(("cls", ""))
            if is_property:
                params_by_name.append(("self", ""))
            found_last_positional = False
            arg_position = 0
            for p, v in sig.parameters.items():
                if is_property and arg_position < 2:
                    continue
                arg_position += 1
                optional_globe = (
                    "**"
                    if v.kind == inspect.Parameter.VAR_KEYWORD
                    else "*"
                    if v.kind == inspect.Parameter.VAR_POSITIONAL
                    else ""
                )
                if v.kind == inspect.Parameter.VAR_POSITIONAL:
                    found_last_positional = True
                if (
                    v.kind == inspect.Parameter.KEYWORD_ONLY
                    and not found_last_positional
                ):
                    params_by_name.append(("*", ""))
                    found_last_positional = True
                default = (
                    ""
                    if v.default == inspect._empty
                    else f" = {v.default.__name__}"
                    if inspect.isclass(v.default)
                    else " = None"
                )
                type_annotation = (
                    ""
                    if v.annotation == inspect._empty
                    else f": {_get_type_info(v.annotation, locals_attrs, additional_classes)}"
                )
                p_name = f"{optional_globe}{p}"
                type_annotation = (
                    type_annotation[: -len(" = None")]
                    if (type_annotation.endswith("= None") and default)
                    else type_annotation
                )
                params_by_name.append((p_name, f"{type_annotation}{default}"))

            params_as_str = ", ".join([f"{k}{v}" for (k, v) in params_by_name])
            method_by_name.append("")
            if method_cls is staticmethod:
                method_by_name.append("@staticmethod")
            elif method_cls is classmethod:
                method_by_name.append("@classmethod")
            elif is_property:
                method_by_name.append("@property")
            method_by_name.append(
                f"def {name}({params_as_str}){return_annotations}: ..."
            )
        except Exception as e:
            logging.warning(e)
            method_by_name.append(f"def {name}(self, *args, **kw): ...")

    return method_by_name


def _get_init(cls, ordered_args: dict) -> str:
    init_params = f",\n{INDENT * 2}".join(
        [f"{INDENT * 2}self"] + [f"{k}: {v}" for k, v in ordered_args.items()]
    )
    kw_opt = (
        f",\n{INDENT * 2}**kw" if getattr(cls, "_additionalProperties", True) else ""
    )
    return f"    def __init__(\n{init_params}{kw_opt}\n{INDENT}): ..."


def _get_shallow_clone(cls, ordered_args: dict) -> str:
    ordered_args_with_none = {}
    for k, v in ordered_args.items():
        ordered_args_with_none[k] = v if v.endswith("= None") else f"{v} = None"
    params = f",\n{INDENT * 2}".join(
        [f"{INDENT * 2}self"] + [f"{k}: {v}" for k, v in ordered_args_with_none.items()]
    )
    kw_opt = (
        f",\n{INDENT * 2}**kw" if getattr(cls, "_additionalProperties", True) else ""
    )
    return f"    def shallow_clone_with_overrides(\n{params}{kw_opt}\n{INDENT}): ..."


def get_stubs_of_structures(
    struct_classe_by_name: dict, local_attrs, additional_classes
) -> list:
    out_src = []
    for cls_name, cls in struct_classe_by_name.items():
        fields_info = _get_all_type_info(
            cls, locals_attrs=local_attrs, additional_classes=additional_classes
        )
        method_info = _get_methods_info(
            cls, locals_attrs=local_attrs, additional_classes=additional_classes
        )

        ordered_args = _get_ordered_args(fields_info)
        out_src.append(f"class {cls_name}(Structure):")
        if not fields_info and not method_info:
            out_src.append(f"{INDENT}pass")
            out_src.append("")
            continue

        out_src.append(_get_init(cls, ordered_args))
        out_src.append("")
        out_src.append(_get_shallow_clone(cls, ordered_args))
        out_src.append("")

        for field_name, type_name in ordered_args.items():
            out_src.append(f"    {field_name}: {type_name}")
        out_src += [f"{INDENT}{m}" for m in method_info]
        out_src.append("\n")
    return out_src


def get_stubs_of_enums(
    enum_classes_by_name: dict, local_attrs, additional_classes
) -> list:
    out_src = []
    for cls_name, cls in enum_classes_by_name.items():

        method_info = _get_methods_info(
            cls, locals_attrs=local_attrs, additional_classes=additional_classes
        )

        out_src.append(f"class {cls_name}(enum.Enum):")
        for v in cls:
            out_src.append(f"{INDENT}{v.name} = enum.auto()")
        out_src.append("")

        out_src.append("")
        out_src += [f"{INDENT}{m}" for m in method_info]
        out_src.append("\n")
    return out_src


def add_imports(local_attrs: dict, additional_classes, existing_imports: set) -> list:
    base_typing = ["Union", "Optional", "Any", "TypeVar", "Type", "NoReturn"]
    typing_types_to_import = [t for t in base_typing if t not in existing_imports]
    base_import_statements = []
    if typing_types_to_import:
        base_import_statements.append(
            f"from typing import {', '.join(typing_types_to_import)}"
        )
    base_import_statements += [
        "from typedpy import Structure",
        "",
    ]
    extra_imports_by_name = _get_mapped_extra_imports(additional_classes)
    extra_imports = {
        f"from {_get_package(v, local_attrs)} import {k}{_as_something(k, local_attrs)}"
        for k, v in extra_imports_by_name.items()
        if (
            (
                k not in local_attrs
                or local_attrs[k].__module__ != local_attrs["__name__"]
            )
            and k not in existing_imports
        )
    }
    return base_import_statements + sorted(extra_imports)


def _get_enum_classes(attrs, only_calling_module):
    return {
        k: v
        for k, v in attrs.items()
        if (
            inspect.isclass(v)
            and issubclass(v, enum.Enum)
            and (v.__module__ == attrs["__name__"] or not only_calling_module)
        )
    }


def _get_other_classes(attrs, only_calling_module):
    res = {}
    for k, v in attrs.items():
        if (
            inspect.isclass(v)
            and not issubclass(v, enum.Enum)
            and not issubclass(v, Structure)
        ):
            res[k] = v

    return res


def _get_functions(attrs, only_calling_module):
    return {
        k: v
        for k, v in attrs.items()
        if (
            inspect.isfunction(v)
            and (v.__module__ == attrs["__name__"] or not only_calling_module)
        )
    }


def _get_type_annotation(
    prefix: str, annotation, default: str, local_attrs, additional_classes
):
    def _correct_for_return_annotation(res: str):
        if "->" in prefix:
            return res[:-7] if res.endswith("= None") else res
        if default:
            cleaned_res = res[: -len(" = None")] if res.endswith("= None") else res
            return f"{cleaned_res}{default}"
        return res

    try:
        res = (
            ""
            if annotation == inspect._empty
            else f"{prefix}{_get_type_info(annotation, local_attrs, additional_classes)}"
        )
        return _correct_for_return_annotation(res)
    except Exception as e:
        logging.exception(e)
        return ""


def get_stubs_of_functions(func_by_name, local_attrs, additional_classes) -> list:
    def _convert_default(d):
        return d.__name__ if inspect.isclass(d) else None

    out_src = []
    for name, func in func_by_name.items():
        sig = inspect.signature(func)
        return_annotations = _get_type_annotation(
            " -> ", sig.return_annotation, "", local_attrs, additional_classes
        )
        params_by_name = []
        found_last_positional = False
        for p, v in sig.parameters.items():
            default = (
                ""
                if v.default == inspect._empty
                else f" = {_convert_default(v.default)}"
            )
            type_annotation = _get_type_annotation(
                ": ", v.annotation, default, local_attrs, additional_classes
            )
            optional_globe = (
                "**"
                if v.kind == inspect.Parameter.VAR_KEYWORD
                else "*"
                if v.kind == inspect.Parameter.VAR_POSITIONAL
                else ""
            )
            if v.kind == inspect.Parameter.VAR_POSITIONAL:
                found_last_positional = True
            if v.kind == inspect.Parameter.KEYWORD_ONLY and not found_last_positional:
                params_by_name.append(("*", ""))
                found_last_positional = True
            p_name = f"{optional_globe}{p}"
            params_by_name.append((p_name, type_annotation))
        params_as_str = ", ".join([f"{k}{v}" for (k, v) in params_by_name])

        out_src.append(f"def {name}({params_as_str}){return_annotations}: ...")
        out_src.append("\n")
    return out_src


def _get_bases(cls, local_attrs, additional_classes) -> list:
    res = []
    for b in cls.__bases__:
        if b is object or b.__module__ == "typing":
            continue
        if not _is_sqlalchemy(b):
            the_type = _get_type_info(b, local_attrs, additional_classes)
            if the_type != "Any":
                res.append(the_type)
    return res


def get_stubs_of_other_classes(
    *, other_classes, local_attrs, additional_classes, additional_imports
):
    out_src = []
    for cls_name, cls in other_classes.items():
        if cls.__module__ != local_attrs["__name__"]:
            if cls_name not in additional_imports:
                out_src += [f"class {cls_name}:", f"{INDENT}pass", ""]
            continue

        bases = _get_bases(cls, local_attrs, additional_classes)
        method_info = _get_methods_info(
            cls, locals_attrs=local_attrs, additional_classes=additional_classes
        )
        bases_str = f"({', '.join(bases)})" if bases else ""
        out_src.append(f"class {cls_name}{bases_str}:")
        if not method_info:
            out_src.append(f"{INDENT}pass")
        out_src.append("")
        out_src += [f"{INDENT}{m}" for m in method_info]
        out_src.append("\n")
    return out_src


def get_typevars(attrs):
    res = [
        f'{k} = TypeVar("{k}")' for k in attrs if isinstance(attrs[k], typing.TypeVar)
    ]
    return [""] + res + [""]


def create_pyi(calling_source_file, attrs: dict, only_current_module: bool = True):
    full_path: Path = Path(calling_source_file)
    pyi_path = (full_path.parent / f"{full_path.stem}.pyi").resolve()
    out_src = []
    additional_imports = []
    imported = list(get_imports(attrs.get("__file__")))
    if only_current_module:
        for level, pkg_name, val_info, alias in imported:
            level_s = "." * level
            val = ".".join(val_info)
            alias = alias or val
            if val and pkg_name:
                if val != "*":
                    out_src.append(f"from {level_s}{pkg_name} import {val} as {alias}")
                    additional_imports.append(alias)
                else:
                    out_src.append(f"from {level_s}{pkg_name} import {val}")
            elif pkg_name:
                out_src.append(f"import {level_s}{pkg_name}")
                additional_imports.append(pkg_name)
            else:
                out_src.append(f"import {level_s}{alias}")
                additional_imports.append(alias)

    enum_classes = _get_enum_classes(attrs, only_calling_module=only_current_module)
    if enum_classes and enum not in additional_imports:
        out_src += ["import enum", ""]
    struct_classes = _get_struct_classes(attrs, only_calling_module=only_current_module)
    other_classes = _get_other_classes(attrs, only_calling_module=only_current_module)
    functions = _get_functions(attrs, only_calling_module=only_current_module)

    out_src += get_typevars(attrs)

    additional_classes = set()
    out_src += _get_consts(
        attrs,
        additional_classes=additional_classes,
        additional_imports=additional_imports,
    )

    out_src += get_stubs_of_enums(
        enum_classes, local_attrs=attrs, additional_classes=additional_classes
    )
    out_src += get_stubs_of_other_classes(
        other_classes=other_classes,
        local_attrs=attrs,
        additional_classes=additional_classes,
        additional_imports=additional_imports,
    )
    out_src += get_stubs_of_structures(
        struct_classes, local_attrs=attrs, additional_classes=additional_classes
    )

    out_src += get_stubs_of_functions(
        functions, local_attrs=attrs, additional_classes=additional_classes
    )

    from_future_import = [
        (i, s) for i, s in enumerate(out_src) if s.startswith("from __future__")
    ]
    for number_of_deletions, (i, s) in enumerate(from_future_import):
        out_src = (
            out_src[: i - number_of_deletions] + out_src[i + 1 - number_of_deletions :]
        )
    out_src = (
        [x[1] for x in from_future_import]
        + add_imports(
            local_attrs=attrs,
            additional_classes=additional_classes,
            existing_imports=set(additional_imports),
        )
        + out_src
    )

    out_src = AUTOGEN_NOTE + out_src
    out_s = "\n".join(out_src)
    with open(pyi_path, "w", encoding="UTF-8") as f:
        f.write(out_s)


def _get_consts(attrs, additional_classes, additional_imports):
    def _is_of_builtin(v) -> bool:
        return isinstance(v, (int, float, str, dict, list, set, complex, bool))

    def _as_builtin(v) -> str:
        return v if isinstance(v, (int, float, str, complex, bool)) else v.__class__()

    res = []
    annotations = attrs.get("__annotations__", None) or {}
    constants = {
        k: v
        for (k, v) in attrs.items()
        if (_is_of_builtin(v) or v is None)
        and not k.startswith("__")
        and k not in additional_imports
    }
    for c in constants:
        the_type = (
            _get_type_info(annotations[c], attrs, additional_classes)
            if c in annotations
            else None
        )
        type_str = f": {the_type}" if the_type else ""
        val = (
            str(wrap_val(_as_builtin(attrs[c])))
            if _is_of_builtin(attrs[c])
            else "None"
            if attrs[c] is None
            else ""
        )
        val_st = f" = {val}" if val else ""
        res.append(f"{c}{type_str}{val_st}")
        res.append("")
    return res


def create_stub_for_file(abs_module_path: str, src_root: str, stubs_root: str = None):
    ext = os.path.splitext(abs_module_path)[-1].lower()
    if ext != ".py":
        return
    stem = Path(abs_module_path).stem
    dir_name = str(Path(abs_module_path).parent)
    relative_dir = relpath(dir_name, src_root)
    package_name = ".".join(Path(relative_dir).parts)
    module_name = stem if stem != "__init__" else package_name
    sys.path.append(str(Path(dir_name).parent))
    sys.path.append(src_root)
    spec = importlib.util.spec_from_file_location(module_name, abs_module_path)
    the_module = importlib.util.module_from_spec(spec)
    if not the_module.__package__:
        the_module.__package__ = package_name
    spec.loader.exec_module(the_module)

    pyi_dir = (
        Path(stubs_root) / Path(relative_dir)
        if stubs_root
        else Path(abs_module_path).parent
    )
    pyi_dir.mkdir(parents=True, exist_ok=True)
    (pyi_dir / Path("__init__.pyi")).touch(exist_ok=True)

    pyi_path = (pyi_dir / f"{stem}.pyi").resolve()
    if not getattr(the_module, "__package__", None):
        the_module.__package__ = ".".join(Path(relative_dir).parts)
    create_pyi(str(pyi_path), the_module.__dict__)



def create_pyi_ast(calling_source_file, pyi_path):
    out_src = ["import datetime", "from typing import Optional, Any, Iterable"]
    additional_imports = []
    imported = list(get_imports(calling_source_file))
    found_sqlalchmy = False
    for level, pkg_name, val_info, alias in imported:
        level_s = "." * level
        val = ".".join(val_info)
        alias = alias or val
        if pkg_name and pkg_name.startswith("sqlalchemy"):
            found_sqlalchmy = True
        if val and pkg_name:
            if val != "*":
                out_src.append(f"from {level_s}{pkg_name} import {val} as {alias}")
                additional_imports.append(alias)
            else:
                out_src.append(f"from {level_s}{pkg_name} import {val}")
        elif pkg_name:
            out_src.append(f"import {level_s}{pkg_name}")
            additional_imports.append(pkg_name)
        else:
            out_src.append(f"import {level_s}{alias}")
            additional_imports.append(alias)

    if found_sqlalchmy:
        out_src.extend([""] * 3)
        models = get_models(calling_source_file)
        out_src += models_to_src(models)
    out_src = AUTOGEN_NOTE + out_src
    out_s = "\n".join(out_src)
    with open(pyi_path, "w", encoding="UTF-8") as f:
        f.write(out_s)


def create_stub_for_file_using_ast(
    abs_module_path: str, src_root: str, stubs_root: str = None
):
    ext = os.path.splitext(abs_module_path)[-1].lower()
    if ext != ".py":
        return
    stem = Path(abs_module_path).stem
    dir_name = str(Path(abs_module_path).parent)
    relative_dir = relpath(dir_name, src_root)
    package_name = ".".join(Path(relative_dir).parts)

    pyi_dir = (
        Path(stubs_root) / Path(relative_dir)
        if stubs_root
        else Path(abs_module_path).parent
    )
    pyi_dir.mkdir(parents=True, exist_ok=True)
    (pyi_dir / Path("__init__.pyi")).touch(exist_ok=True)

    pyi_path = (pyi_dir / f"{stem}.pyi").resolve()
    create_pyi_ast(abs_module_path, str(pyi_path))

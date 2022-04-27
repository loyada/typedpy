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
from .utility import type_is_generic

builtins_types = [
    getattr(builtins, k)
    for k in dir(builtins)
    if isinstance(getattr(builtins, k), type)
]

INDENT = " " * 4

AUTOGEN_NOTE = [
    "",
    "#### This stub was autogenerated by Typedpy",
    "###########################################",
    "",
]


def _get_package(v, attrs):
    pkg_name = attrs.get("__package__") or "%^$%^$%^#"
    if v.startswith(pkg_name):
        return v[len(pkg_name) :]
    return v


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
        # args_st = "" if not mapped_args else f"[{','.join(mapped_args)}]"
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


def _get_type_info(field, locals_attrs, additional_classes):
    try:
        if field is ...:
            return "..."
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
            and not the_type.__module__.startswith("typedpy")
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
    return [
        f"from {_get_package(v.__module__, attrs)} import {k}{_as_something(k, attrs)}"
        for k, v in attrs.items()
        if (
            inspect.isclass(v)
            and attrs["__name__"] != v.__module__
            and not v.__module__.startswith("typing")
            and not v.__module__.startswith("typedpy")
        )
    ]


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
                    or (inspect.isclass(c) and issubclass(c, Field))
                    else c.__module__
                    if name != "Any"
                    else None
                )
            if module_name:
                mapped[name] = module_name
        except Exception as e:
            logging.exception(e)
    return mapped


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
        if getattr(attr, "__module__", "") == "sqlalchemy.orm.attributes":
            attrs.append(attribute)
            continue
        is_func = not inspect.isclass(attr) and (
            callable(attr) or isinstance(attr, (property, classmethod, staticmethod))
        )
        if not any([attr is None, inspect.isclass(attr), is_func, isinstance(attr, cls), issubclass(cls, Structure)]):
            attrs.append(attribute)
            continue

        if (
            is_func
            and attribute not in all_fields
            and attribute not in ignored_methods
        ):
            method_list.append(attribute)

    if (
        not issubclass(cls, Structure)
        and not issubclass(cls, enum.Enum)
        and "__init__" in members
    ):
        method_list = ["__init__"] + method_list

    for name in cls_dict.get("__annotations__",{}):
        if name not in attrs and not issubclass(cls, Structure):
            attrs.append(name)
    return method_list, attrs


def _get_methods_info(cls, locals_attrs, additional_classes) -> list:
    method_by_name = []
    mros = list(reversed(inspect.getmro(cls)))[1:]
    members = {}
    for c in mros:
        members.update(dict(c.__dict__))
        annotations = c.__dict__.get("__annotations__", {})
        for a in annotations:
            members[a] = annotations[a]
        members.update(annotations)

    method_list, cls_attrs = _get_method_and_attr_list(cls, members)

    for attr in cls_attrs:
        the_type = members.get(attr, None)
        resolved_type = _get_type_info(the_type, locals_attrs, additional_classes) if the_type else "Any"

        method_by_name.append(f"{attr}: {resolved_type}")
    cls_dict = cls.__dict__

    for name in method_list:
        method_cls = members[name].__class__
        is_property = False
        func = cls_dict.get(name) if name in cls_dict else getattr(cls, name, None)
        func = getattr(cls, name) if isinstance(func, (classmethod, staticmethod, property)) else func
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
                    else f" = {v.default}"
                    if not inspect.isclass(v.default)
                    else f" = {v.default.__name__}"
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

        if not fields_info and not method_info:
            continue

        ordered_args = _get_ordered_args(fields_info)
        out_src.append(f"class {cls_name}(Structure):")
        out_src.append(_get_init(cls, ordered_args))
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
    base_import_statements = [
        "from typing import Union, Optional, Any, TypeVar, Type, NoReturn",
        "from typedpy import Structure",
        "import enum",
        "",
    ]
    extra_imports_by_name = _get_mapped_extra_imports(additional_classes)
    extra_imports = {
        f"from {_get_package(v, local_attrs)} import {k}{_as_something(k, local_attrs)}"
        for k, v in extra_imports_by_name.items()
        if (
            k not in local_attrs or local_attrs[k].__module__ != local_attrs["__name__"]
        )
    } - existing_imports
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
    return {
        k: v
        for k, v in attrs.items()
        if (
            inspect.isclass(v)
            and not issubclass(v, enum.Enum)
            and not issubclass(v, Structure)
            and (v.__module__ == attrs["__name__"] or not only_calling_module)
        )
    }


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
        return d.__name__ if inspect.isclass(d) else d

    out_src = []
    for name, func in func_by_name.items():
        sig = inspect.signature(func)
        return_annotations = _get_type_annotation(
            " -> ", sig.return_annotation, "", local_attrs, additional_classes
        )
        params_by_name = []
        found_keyword_only = False
        for p, v in sig.parameters.items():
            if not found_keyword_only and v.kind == inspect.Parameter.KEYWORD_ONLY:
                found_keyword_only = True
                params_by_name.append(("*", ""))
            default = (
                ""
                if v.default == inspect._empty
                else f" = {_convert_default(v.default)}"
            )
            type_annotation = _get_type_annotation(
                ": ", v.annotation, default, local_attrs, additional_classes
            )
            params_by_name.append((p, type_annotation))
        params_as_str = ", ".join([f"{k}{v}" for (k, v) in params_by_name])

        out_src.append(f"def {name}({params_as_str}){return_annotations}: ...")
        out_src.append("\n")
    return out_src


def _get_bases(cls, local_attrs, additional_classes) -> list:
    res = []
    for b in cls.__bases__:
        if b is object:
            continue
        the_type = _get_type_info(b, local_attrs, additional_classes)
        if the_type!="Any":
            res.append(the_type)
    return res


def get_stubs_of_other_classes(other_classes, local_attrs, additional_classes):
    out_src = []
    for cls_name, cls in other_classes.items():
        bases = _get_bases(cls, local_attrs, additional_classes)
        method_info = _get_methods_info(
            cls, locals_attrs=local_attrs, additional_classes=additional_classes
        )

        if not method_info:
            continue
        bases_str = f"({', '.join(bases)})" if bases else ""
        out_src.append(f"class {cls_name}{bases_str}:")
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
    if only_current_module:
        additional_imports = _get_imported_classes(attrs)
        if additional_imports:
            additional_imports.append("")
        out_src += additional_imports

    enum_classes = _get_enum_classes(attrs, only_calling_module=only_current_module)
    struct_classes = _get_struct_classes(attrs, only_calling_module=only_current_module)
    other_classes = _get_other_classes(attrs, only_calling_module=only_current_module)
    functions = _get_functions(attrs, only_calling_module=only_current_module)
    out_src += get_typevars(attrs)

    additional_classes = set()
    out_src += get_stubs_of_enums(
        enum_classes, local_attrs=attrs, additional_classes=additional_classes
    )
    out_src += get_stubs_of_other_classes(
        other_classes, local_attrs=attrs, additional_classes=additional_classes
    )
    out_src += get_stubs_of_structures(
        struct_classes, local_attrs=attrs, additional_classes=additional_classes
    )

    out_src += get_stubs_of_functions(
        functions, local_attrs=attrs, additional_classes=additional_classes
    )

    out_src = (
        add_imports(
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

import enum
import importlib.util
import inspect
import os
import typing
from os.path import relpath
from pathlib import Path
from .fields import AnyOf, FunctionCall, Map
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

INDENT = " " * 4

AUTOGEN_NOTE = [
    "",
    "#### This stub was autogenerated by Typedpy",
    "###########################################",
    "",
]


def _get_anyof_typing(field, locals_attrs, additional_classes):
    union_fields = getattr(field, "_fields", [])
    if len(union_fields) == 2 and isinstance(union_fields[1], NoneField):
        info = _get_type_info(union_fields[0], locals_attrs, additional_classes)
        return f"Optional[{info}] = None"

    fields = ",".join(
        [_get_type_info(f, locals_attrs, additional_classes) for f in union_fields]
    )
    return f"Union[{fields}]"


def _get_type_info(field, locals_attrs, additional_classes):
    if isinstance(field, AnyOf):
        return _get_anyof_typing(field, locals_attrs, additional_classes)

    if isinstance(field, Map):
        if not field.items:
            return "dict"
        sub_types = ", ".join(
            [_get_type_info(f, locals_attrs, additional_classes) for f in field.items]
        )
        return f"dict[{sub_types}]"

    if isinstance(field, Enum):
        if field._is_enum:
            additional_classes.add(field._enum_class)
            return field._enum_class.__name__

    the_type = getattr(field, "get_type", field) if isinstance(field, Field) else field
    if the_type is typing.Any:
        return "Any"
    if (
            not the_type.__module__.startswith("typedpy")
            and the_type.__module__ != "builtins"
            and the_type not in locals_attrs
            and not type_is_generic(the_type)
    ):
        additional_classes.add(field)
    if type_is_generic(the_type):
        origin = getattr(the_type, "__origin__", None)
        if origin in {list, set, tuple}:
            args = getattr(the_type, "__args__", None)
            if len(args)!=1:
                return str(origin)
            return f"{origin.__name__}[{_get_type_info(args[0], locals_attrs, additional_classes)}]"
        return _get_type_info(
            get_typing_lib_info(field), locals_attrs, additional_classes
        )

    return f"{the_type.__name__}"


def _get_all_type_info(cls, locals_attrs, additional_classes) -> dict:
    type_by_name = {}
    required = getattr(cls, "_required", None)
    for field_name, field in cls.get_all_fields_by_name().items():
        type_info_str: str = _get_type_info(field, locals_attrs, additional_classes)
        if (
                field_name not in required
                and required is not None
                and not type_info_str.startswith("Optional[")
        ):
            type_info_str = f"Optional[{type_info_str}] = None"
        type_by_name[field_name] = type_info_str

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
        f"from {v.__module__} import {k}"
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
                )
            mapped[name] = module_name
        except Exception as e:
            print(f"Error: {e}")
    return mapped


def _get_methods_info(cls, locals_attrs, additional_classes) -> list:
    method_by_name = []
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
    mros = list(reversed(inspect.getmro(cls)))[1:]
    members = {}
    for c in mros:
        members.update(dict(c.__dict__))
    method_list = [
        attribute
        for attribute in members
        if (callable(getattr(cls, attribute, None)) or isinstance(getattr(cls, attribute, None), property))
           and not attribute.startswith("_")
           and attribute not in all_fields
           and attribute not in ignored_methods
    ]
    if not issubclass(cls, Structure) and not issubclass(cls, enum.Enum) and "__init__" in members:
        method_list = ["__init__"] + method_list

    for name in method_list:
        method_cls = members[name].__class__
        is_property = False
        func = getattr(cls, name)
        if isinstance(func, property):
            is_property = True
            func = func.__get__
        sig = inspect.signature(func)
        return_annotations = (
            ""
            if sig.return_annotation == inspect._empty
            else f" -> {_get_type_info(sig.return_annotation, locals_attrs, additional_classes)}"
        )
        params_by_name = {}
        if method_cls is classmethod:
            params_by_name["cls"] = ""
        for p, v in sig.parameters.items():
            optional_globe = "**" if v.kind==inspect.Parameter.VAR_KEYWORD else "*" if v.kind==inspect.Parameter.VAR_POSITIONAL else ""
            default = "" if v.default == inspect._empty else f" = {v.default}"
            type_annotation = (
                ""
                if v.annotation == inspect._empty
                else f": {_get_type_info(v.annotation, locals_attrs, additional_classes)}"
            )
            p_name = f"{optional_globe}{p}"
            params_by_name[p_name] = f"{type_annotation}{default}"
        if is_property:
            params_by_name.pop("owner")
            params_by_name.pop("instance")
            params_by_name["self"] = ""
        params_as_str = ", ".join([f"{k}{v}" for k, v in params_by_name.items()])
        method_by_name.append("")
        if method_cls is staticmethod:
            method_by_name.append("@staticmethod")
        elif method_cls is classmethod:
            method_by_name.append("@classmethod")
        elif is_property:
            method_by_name.append("@property")
        method_by_name.append(f"def {name}({params_as_str}){return_annotations}: ...")

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


def add_imports(local_attrs: dict, additional_classes) -> list:
    base_import_statements = [
        "from typing import Union, Optional, Any",
        "from typedpy import Structure",
        "import enum",
        "",
    ]
    extra_imports_by_name = _get_mapped_extra_imports(additional_classes)
    extra_imports = sorted(
        [
            f"from {v} import {k}"
            for k, v in extra_imports_by_name.items()
            if k not in local_attrs
        ]
    )
    return base_import_statements + extra_imports


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


def get_stubs_of_functions(func_by_name, local_attrs, additional_classes) -> list:
    out_src = []
    for name, func in func_by_name.items():
        sig = inspect.signature(func)
        return_annotations = (
            ""
            if sig.return_annotation == inspect._empty
            else f" -> {_get_type_info(sig.return_annotation, local_attrs, additional_classes)}"
        )
        params_by_name = {}
        for p, v in sig.parameters.items():
            default = "" if v.default == inspect._empty else f" = {v.default}"
            type_annotation = (
                ""
                if v.annotation == inspect._empty
                else f": {_get_type_info(v.annotation, local_attrs, additional_classes)}"
            )
            params_by_name[p] = f"{type_annotation}{default}"
        params_as_str = ", ".join([f"{k}{v}" for k, v in params_by_name.items()])

        out_src.append(f"def {name}({params_as_str}){return_annotations}: ...")
        out_src.append("\n")
    return out_src


def get_stubs_of_other_classes(other_classes, local_attrs, additional_classes):
    out_src = []
    for cls_name, cls in other_classes.items():
        method_info = _get_methods_info(
            cls, locals_attrs=local_attrs, additional_classes=additional_classes
        )

        if not method_info:
            continue

        out_src.append(f"class {cls_name}:")
        out_src.append("")
        out_src += [f"{INDENT}{m}" for m in method_info]
        out_src.append("\n")
    return out_src


def create_pyi(calling_source_file, attrs: dict, only_current_module: bool = True):
    full_path: Path = Path(calling_source_file)
    pyi_path = (full_path.parent / f"{full_path.stem}.pyi").resolve()
    out_src = []

    if only_current_module:
        additional_imports = _get_imported_classes(attrs)
        if additional_imports:
            additional_imports.append("")
        out_src += additional_imports

    enum_classes = _get_enum_classes(attrs, only_calling_module=only_current_module)
    struct_classes = _get_struct_classes(attrs, only_calling_module=only_current_module)
    other_classes = _get_other_classes(attrs, only_calling_module=only_current_module)
    functions = _get_functions(attrs, only_calling_module=only_current_module)

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
            add_imports(local_attrs=attrs, additional_classes=additional_classes) + out_src
    )

    out_src = AUTOGEN_NOTE + out_src
    out_s = "\n".join(out_src)
    with open(pyi_path, "w", encoding="UTF-8") as f:
        f.write(out_s)


def create_stub_for_file(abs_module_path: str, src_root: str, stubs_root: str = None):
    ext = os.path.splitext(abs_module_path)[-1].lower()
    if ext != ".py":
        return
    module_name = Path(abs_module_path).stem
    relative_dir = relpath(str(Path(abs_module_path).parent), src_root)
    spec = importlib.util.spec_from_file_location(module_name, abs_module_path)
    the_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(the_module)

    pyi_dir = (
        Path(stubs_root) / Path(relative_dir)
        if stubs_root
        else Path(abs_module_path).parent
    )
    pyi_dir.mkdir(parents=True, exist_ok=True)
    (pyi_dir / Path("__init__.pyi")).touch(exist_ok=True)

    pyi_path = (pyi_dir / f"{module_name}.pyi").resolve()
    create_pyi(str(pyi_path), the_module.__dict__)

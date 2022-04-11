import typing
from pathlib import Path
import inspect

from . import AnyOf, Deserializer, Enum, FunctionCall, Map, Serializer
from .structures import ImmutableStructure, NoneField, TypedField, Structure

INDENT = "    "


def _get_type_info(field):
    if isinstance(field, AnyOf):
        union_fields = getattr(field, "_fields", [])
        if len(union_fields) == 2 and isinstance(union_fields[1], NoneField):
            return f"Optional[{_get_type_info(union_fields[0])}] = None"

        fields = ",".join([_get_type_info(f) for f in union_fields])
        return f"Union[{fields}]"

    if isinstance(field, Map):
        sub_types = ", ".join([_get_type_info(f) for f in field.items])
        return f"dict[{sub_types}]"

    if isinstance(field, Enum):
        if field._is_enum:
            return field._enum_class.__name__

    the_type = field.get_type
    if the_type is typing.Any:
        return "Any"

    return f"{the_type.__name__}"


def _get_all_type_info(cls) -> dict:
    type_by_name = {}
    required = getattr(cls, "_required", None)
    for field_name, field in cls.get_all_fields_by_name().items():
        type_info_str: str = _get_type_info(field)
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
            and (v.__module__ == attrs['__name__'] or not only_calling_module)
            and v not in {Deserializer, Serializer, ImmutableStructure, FunctionCall}
        )
    }


def _get_imported_classes(attrs):
    return [
        f"from {v.__module__} import {k}"
        for k, v in attrs.items()
        if (
            inspect.isclass(v)
            and attrs['__name__'] != v.__module__
            and not v.__module__.startswith('typing')
            and not v.__module__.startswith('typedpy')
        )
    ]


def _get_ordered_args(unordered_args: dict):
    optional_args = {k:v for k,v in unordered_args.items() if v.endswith("= None")}
    mandatory_args = {k:v for k,v in unordered_args.items() if k not in optional_args}
    return {**mandatory_args, **optional_args}


def create_pyi(calling_source_file, attrs: dict, only_current_module: bool = True):
    full_path: Path = Path(calling_source_file)
    pyi_path = (full_path.parent / f"{full_path.stem}.pyi").resolve()

    out_src = [
        "from typedpy import Structure",
        "from typing import Union, Optional, Any",
        "",
    ]
    if only_current_module:
        additional_imports = _get_imported_classes(attrs)
        if additional_imports:
            additional_imports.append("")
        out_src += additional_imports

    struct_classes = _get_struct_classes(attrs, only_calling_module=only_current_module)

    for cls_name, cls in struct_classes.items():
        info = _get_all_type_info(cls)
        if not info:
            continue

        ordered_args = _get_ordered_args(info)
        out_src.append(f"class {cls_name}(Structure):")
        init_params = f",\n{INDENT*2}".join([f"{k}: {v}" for k, v in ordered_args.items()])
        kw_opt = (
            f",\n{INDENT*2}**kw" if getattr(cls, "_additionalProperties", True) else ""
        )
        out_src.append(f"    def __init__(self, {init_params}{kw_opt}\n{INDENT}): ...")
        out_src.append("")

        for field_name, type_name in ordered_args.items():
            out_src.append(f"    {field_name}: {type_name}")
        out_src.append("\n")

    out_s = "\n".join(out_src)
    with open(pyi_path, "w", encoding="UTF-8") as f:
        f.write(out_s)

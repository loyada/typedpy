from pathlib import Path
import inspect
from typing import Union

from . import AnyOf, Deserializer, FunctionCall, Map, Serializer
from .structures import ImmutableStructure, NoneField, TypedField, Structure

INDENT = "    "


def _get_type_info(field):
    if isinstance(field, AnyOf):
        union_fields = getattr(field, "_fields", [])
        if len(union_fields) == 2 and isinstance(union_fields[1], NoneField):
            return f"Optional[{_get_type_info(union_fields[0])}]"

        fields = ",".join([_get_type_info(f) for f in union_fields])
        return f"Union[{fields}]"

    if isinstance(field, Map):
        sub_types = ", ".join([_get_type_info(f) for f in field.items])
        return f"dict[{sub_types}]"
    the_type = field.get_type

    return f"{the_type.__name__}"


def _get_all_type_info(cls) -> dict[str, str]:
    type_by_name = {}
    required = getattr(cls, "_required", None)
    for field_name, field in cls.get_all_fields_by_name().items():
        type_info_str: str = _get_type_info(field)
        if (
            field_name not in required
            and required is not None
            and not type_info_str.startswith("Optional[")
        ):
            type_info_str = f"Optional[{type_info_str}]"
        type_by_name[field_name] = type_info_str

    return type_by_name


def _get_struct_classes(attrs):
    return {
        k: v
        for k, v in attrs.items()
        if (
            inspect.isclass(v)
            and issubclass(v, Structure)
            and v not in {Deserializer, Serializer, ImmutableStructure, FunctionCall}
        )
    }


def create_pyi(calling_source_file, attrs: dict):
    full_path: Path = Path(calling_source_file)
    pyi_path = (full_path.parent / f"{full_path.stem}.pyi").resolve()

    out_src = [
        "from typedpy import Structure",
        "from typing import Union, Optional, Any",
        "",
    ]
    struct_classes = _get_struct_classes(attrs)

    for cls_name, cls in struct_classes.items():
        info = _get_all_type_info(cls)
        if not info:
            continue

        out_src.append(f"class {cls_name}(Structure):")
        init_params = f",\n{INDENT*2}".join([f"{k}: {v}" for k, v in info.items()])
        kw_opt = (
            f",\n{INDENT*2}**kw" if getattr(cls, "_additionalProperties", True) else ""
        )
        out_src.append(f"    def __init__(self, {init_params}{kw_opt}\n{INDENT}): ...")
        out_src.append("")

        for field_name, type_name in info.items():
            out_src.append(f"    {field_name}: {type_name}")
        out_src.append("\n")

    out_s = "\n".join(out_src)
    with open(pyi_path, "w", encoding="UTF-8") as f:
        f.write(out_s)

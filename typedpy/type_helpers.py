import inspect
import typing
from pathlib import Path
from . import AnyOf, Deserializer, Enum, FunctionCall, Map, Serializer
from .structures import ImmutableStructure, NoneField, Structure, Field

INDENT = "    "


def _get_type_info(field, locals_attrs, additional_classes):

    if isinstance(field, AnyOf):
        union_fields = getattr(field, "_fields", [])
        if len(union_fields) == 2 and isinstance(union_fields[1], NoneField):
            return f"Optional[{_get_type_info(union_fields[0],locals_attrs, additional_classes)}] = None"

        fields = ",".join(
            [_get_type_info(f, locals_attrs, additional_classes) for f in union_fields]
        )
        return f"Union[{fields}]"

    if isinstance(field, Map):
        sub_types = ", ".join(
            [_get_type_info(f, locals_attrs, additional_classes) for f in field.items]
        )
        return f"dict[{sub_types}]"

    if isinstance(field, Enum):
        if field._is_enum:
            return field._enum_class.__name__



    the_type = getattr(field, 'get_type', field) if isinstance(field, Field) else field
    if the_type is typing.Any:
        return "Any"

    if (
        not the_type.__module__.startswith("typedpy")
        and the_type.__module__ != "builtins"
        and the_type not in locals_attrs
    ):
        additional_classes.add(field)
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

    method_list = [attribute for attribute in dir(cls) if
                   callable(getattr(cls, attribute)) and not attribute.startswith('_') and attribute not in cls.get_all_fields_by_name()
                   and attribute not in dir(Structure)]

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
                module_name = c.get_type.__module__
            mapped[name] = module_name
        except Exception as e:
            print(f"Error: {e}")
    return mapped

    # [f"from {cls.__module__} import {cls.get_type}" for cls in additional_classes]


def _get_methods_info(cls, locals_attrs, additional_classes) -> list:
    method_by_name = []
    method_list = [attribute for attribute in dir(cls) if
                   callable(getattr(cls, attribute)) and not attribute.startswith('_') and attribute not in cls.get_all_fields_by_name()
                   and attribute not in dir(Structure)]

    for name in method_list:
        func = getattr(cls, name)
        sig = inspect.signature(func)
        return_annotations = '' if sig.return_annotation==inspect._empty else f" -> {_get_type_info(sig.return_annotation, locals_attrs, additional_classes)}"
        params_by_name = {}
        for p, v in sig.parameters.items():
            default = '' if v.default==inspect._empty else f" = {v.default}"
            type_annotation = '' if v.annotation==inspect._empty else f": {_get_type_info(v.annotation, locals_attrs, additional_classes)}"
            params_by_name[p] = f"{type_annotation}{default}"
        params_as_str = ', '.join([f"{k}{v}" for k,v in params_by_name.items()])
        method_by_name.append("")
        method_by_name.append( f"def {name}({params_as_str}){return_annotations}: ...")

    return method_by_name



def create_pyi(calling_source_file, attrs: dict, only_current_module: bool = True):
    full_path: Path = Path(calling_source_file)
    pyi_path = (full_path.parent / f"{full_path.stem}.pyi").resolve()

    out_src = [
        "from typing import Union, Optional, Any",
        "from typedpy import Structure",
        "",
    ]
    if only_current_module:
        additional_imports = _get_imported_classes(attrs)
        if additional_imports:
            additional_imports.append("")
        out_src += additional_imports

    struct_classes = _get_struct_classes(attrs, only_calling_module=only_current_module)

    additional_classes = set()
    for cls_name, cls in struct_classes.items():
        fields_info = _get_all_type_info(
            cls, locals_attrs=attrs, additional_classes=additional_classes
        )
        method_info = _get_methods_info(cls,  locals_attrs=attrs, additional_classes=additional_classes)

        if not fields_info and not method_info:
            continue

        ordered_args = _get_ordered_args(fields_info)
        out_src.append(f"class {cls_name}(Structure):")
        init_params = f",\n{INDENT*2}".join(
            [f"{k}: {v}" for k, v in ordered_args.items()]
        )
        kw_opt = (
            f",\n{INDENT*2}**kw" if getattr(cls, "_additionalProperties", True) else ""
        )
        out_src.append(f"    def __init__(self, {init_params}{kw_opt}\n{INDENT}): ...")
        out_src.append("")

        for field_name, type_name in ordered_args.items():
            out_src.append(f"    {field_name}: {type_name}")
        out_src += [f"{INDENT}{m}" for m in method_info]
        out_src.append("\n")

    if additional_classes:
        extra_imports_by_name = _get_mapped_extra_imports(additional_classes)
        extra_imports = [
            f"from {v} import {k}"
            for k, v in extra_imports_by_name.items()
            if k not in attrs
        ]
        out_src = out_src[:2] + extra_imports + out_src[2:]
    out_s = "\n".join(out_src)
    with open(pyi_path, "w", encoding="UTF-8") as f:
        f.write(out_s)

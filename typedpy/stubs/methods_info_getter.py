import dataclasses
import enum
import inspect
import logging
from typing import Callable

from typedpy.commons import INDENT, default_factories
from typedpy.utility import type_is_generic
from typedpy.structures import (
    ADDITIONAL_PROPERTIES,
    Field,
    Structure,
)
from typedpy.stubs.type_info_getter import (
    get_type_info,
    is_typeddict,
)
from typedpy.stubs.types_ast import (
    extract_attributes_from_init,
)
from typedpy.stubs.utils import (
    get_optional_globe,
    get_sqlalchemy_init,
    is_not_generic_and_private_class_or_module,
    is_sqlalchemy,
    is_sqlalchemy_orm_model,
    skip_sqlalchemy_attribute,
    try_extract_column_type,
)


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
        if attribute.startswith(private_prefix) and attribute not in {
            "__init__",
            "__call__",
        }:
            continue
        attr = (
            cls_dict.get(attribute)
            if attribute in cls_dict
            else getattr(cls, attribute, None)
        )
        if is_sqlalchemy(attr):
            if not skip_sqlalchemy_attribute(attribute):
                members[attribute] = try_extract_column_type(attr)
                attrs.append(attribute)
            continue
        is_func = not inspect.isclass(attr) and (
            callable(attr) or isinstance(attr, (property, classmethod, staticmethod))
        )
        if all(
            [
                attr is not None,
                not inspect.isclass(attr),
                not is_func,
                not (is_typeddict(cls) or isinstance(attr, cls)),
                not (issubclass(cls, Structure) and attribute.startswith("_")),
            ]
        ):
            attrs.append(attribute)
            continue

        if (
            is_func
            and attribute not in all_fields
            and (
                attribute not in ignored_methods
                or (issubclass(cls, Structure) and attribute == "__init__")
            )
        ):
            method_list.append(attribute)

    if (
        not issubclass(cls, Structure)
        and not issubclass(cls, enum.Enum)
        and "__init__" in members
        and "__init__" not in method_list
    ):
        method_list = ["__init__"] + method_list

    for name in cls_dict.get("__annotations__", {}):
        if name not in attrs:
            attrs.append(name)
    return method_list, attrs


def _get_cls_members_and_annotations(cls):
    members = {}
    members.update(dict(cls.__dict__))
    annotations = cls.__dict__.get("__annotations__", {})
    for a in annotations:
        members[a] = annotations[a]
    members.update(annotations)
    return members


def _get_attributes_with_resolved_type(
    *, members, cls_attrs, locals_attrs, additional_classes
):
    attributes_with_type = []

    for attr in cls_attrs:
        the_type = members.get(attr, None)
        if is_not_generic_and_private_class_or_module(the_type):
            continue
        if inspect.isclass(the_type) or type_is_generic(the_type):
            resolved_type = (
                get_type_info(the_type, locals_attrs, additional_classes)
                if the_type
                else "Any"
            )
        else:
            resolved_type = (
                get_type_info(the_type.__class__, locals_attrs, additional_classes)
                if the_type is not None
                else "Any"
            )
        attributes_with_type.append((attr, resolved_type))

    return attributes_with_type


@dataclasses.dataclass
class FunctionInfo:
    is_property: bool
    func: Callable


def _get_func_info(*, cls, name):
    cls_dict = cls.__dict__
    func_attr = cls_dict.get(name) if name in cls_dict else getattr(cls, name, None)
    func = (
        getattr(cls, name)
        if isinstance(func_attr, (classmethod, staticmethod, property))
        and not is_sqlalchemy(func_attr)
        else func_attr
    )
    is_property = isinstance(func, property)
    return FunctionInfo(
        is_property=is_property, func=func.fget if is_property else func
    )


def _get_list_of_params_with_type(
    *, method_cls, func_info: FunctionInfo, locals_attrs, additional_classes
):
    sig = inspect.signature(func_info.func)
    params_by_name = []
    if method_cls is classmethod:
        params_by_name.append(("cls", ""))
    if func_info.is_property:
        params_by_name.append(("self", ""))
    found_last_positional = False
    arg_position = 0
    for p, v in sig.parameters.items():
        if func_info.is_property and arg_position < 2:
            continue
        arg_position += 1
        if v.kind == inspect.Parameter.VAR_POSITIONAL:
            found_last_positional = True
        if v.kind == inspect.Parameter.KEYWORD_ONLY and not found_last_positional:
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
            else f": {get_type_info(v.annotation, locals_attrs, additional_classes)}"
        )
        p_name = f"{get_optional_globe(v)}{p}"
        type_annotation = (
            type_annotation[: -len(" = None")]
            if (type_annotation.endswith("= None") and default)
            else type_annotation
        )
        params_by_name.append((p_name, f"{type_annotation}{default}"))

    return params_by_name


def _append_special_methods_to_code(
    *, method_cls, func_info: FunctionInfo, method_code
):
    if method_cls is staticmethod:
        method_code.append("@staticmethod")
    elif method_cls is classmethod:
        method_code.append("@classmethod")
    elif func_info.is_property:
        method_code.append("@property")


def _extract_init_of_external_class(
    *, init, attributes_with_type, method_code, locals_attrs, additional_classes
):
    try:
        source = inspect.getsource(init)
        init_type_by_attr = extract_attributes_from_init(
            source, locals_attrs, additional_classes
        )
        for attr_name, attr_type in init_type_by_attr.items():
            if attr_name not in dict(attributes_with_type):
                method_code.insert(0, f"{attr_name}: {attr_type}")
    except:
        logging.info("no __init__ implementation found")


def _get_method_code(
    *, cls, name, attributes_with_type, members, locals_attrs, additional_classes
) -> list:
    method_cls = members[name].__class__
    func_info = _get_func_info(cls=cls, name=name)
    method_code = []
    try:
        return_annotations = _get_return_annotations(
            func=func_info.func,
            locals_attrs=locals_attrs,
            additional_classes=additional_classes,
        )
        if is_sqlalchemy_orm_model(cls) and name == "__init__":
            return get_sqlalchemy_init(attributes_with_type)

        params_by_name = _get_list_of_params_with_type(
            method_cls=method_cls,
            func_info=func_info,
            locals_attrs=locals_attrs,
            additional_classes=additional_classes,
        )
        params_as_str = ", ".join([f"{k}{v}" for (k, v) in params_by_name])
        method_code.append("")
        _append_special_methods_to_code(
            method_cls=method_cls, func_info=func_info, method_code=method_code
        )
        method_code.append(f"def {name}({params_as_str}){return_annotations}: ...")
        if name == "__init__" and not issubclass(cls, Structure):
            _extract_init_of_external_class(
                init=members[name],
                attributes_with_type=attributes_with_type,
                method_code=method_code,
                locals_attrs=locals_attrs,
                additional_classes=additional_classes,
            )

    except Exception as e:
        logging.warning(e)
        method_code.append(f"def {name}(self, *args, **kw): ...")

    return method_code


def _get_return_annotations(*, func, additional_classes, locals_attrs):
    sig = inspect.signature(func)
    return (
        ""
        if sig.return_annotation == inspect._empty
        else " -> None"
        if sig.return_annotation is None
        else f" -> {get_type_info(sig.return_annotation, locals_attrs, additional_classes)}"
    )


@default_factories
def get_methods_and_attributes_as_code(
    cls, locals_attrs, additional_classes, ignore_attributes=set
) -> list:
    members = _get_cls_members_and_annotations(cls)
    method_list, cls_attrs_draft = _get_method_and_attr_list(cls, members)
    cls_attrs = [a for a in cls_attrs_draft if a not in ignore_attributes]
    attributes_with_type = _get_attributes_with_resolved_type(
        members=members,
        cls_attrs=cls_attrs,
        locals_attrs=locals_attrs,
        additional_classes=additional_classes,
    )
    methods_and_attriutes_code = [
        f"{attr}: {resolved_type}" for (attr, resolved_type) in attributes_with_type
    ]

    for name in method_list:
        method_code = _get_method_code(
            cls=cls,
            members=members,
            name=name,
            attributes_with_type=attributes_with_type,
            locals_attrs=locals_attrs,
            additional_classes=additional_classes,
        )
        methods_and_attriutes_code.extend(method_code)

    return methods_and_attriutes_code


def get_additional_structure_methods(
    cls, ordered_args: dict, additional_properties_default: bool
) -> str:
    ordered_args_with_none = {}
    for k, v in ordered_args.items():
        ordered_args_with_none[k] = v if v.endswith("= None") else f"{v} = None"
    params = [f"{k}: {v}" for k, v in ordered_args_with_none.items()]
    params_with_self = f",\n{INDENT * 2}".join([f"{INDENT * 2}self"] + params)
    kw_opt = (
        f",\n{INDENT * 2}**kw"
        if getattr(cls, ADDITIONAL_PROPERTIES, additional_properties_default)
        else ""
    )
    shallow_clone = f"    def shallow_clone_with_overrides(\n{params_with_self}{kw_opt}\n{INDENT}): ..."

    params_with_cls = f",\n{INDENT * 2}".join(
        [f"{INDENT}cls", "source_object: Any", "*"]
        + ["ignore_props: Iterable[str] = None"]
        + params
    )

    from_other_class = f"\n{INDENT}".join(
        [
            "",
            "@classmethod",
            "def from_other_class(",
            f"{params_with_cls}{kw_opt}\n{INDENT}): ...",
        ]
    )
    params_with_cls_none_default = f",\n{INDENT * 2}".join(
        [f"{INDENT}cls", "source_object: Any = None", "*"]
        + ["ignore_props: Iterable[str] = None"]
        + params
    )
    from_trusted_data = f"\n{INDENT}".join(
        [
            "",
            "@classmethod",
            "def from_trusted_data(",
            f"{params_with_cls_none_default}{kw_opt}\n{INDENT}): ...",
        ]
    )
    return "\n".join([shallow_clone, from_other_class, from_trusted_data])


def get_init(cls, ordered_args: dict, additional_properties_default: bool) -> str:
    init_params = f",\n{INDENT * 2}".join(
        [f"{INDENT * 2}self"] + [f"{k}: {v}" for k, v in ordered_args.items()]
    )
    kw_opt = (
        f",\n{INDENT * 2}**kw"
        if getattr(cls, ADDITIONAL_PROPERTIES, additional_properties_default)
        else ""
    )
    return f"    def __init__(\n{init_params}{kw_opt}\n{INDENT}): ..."

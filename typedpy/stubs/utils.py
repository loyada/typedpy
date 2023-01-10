import inspect
import logging
import typing

from typedpy.commons import INDENT, nested
from typedpy.utility import type_is_generic

_private_to_public_pkg = {"werkzeug.localxxx": "flask"}


def is_sqlalchemy(attr):
    module_name = getattr(attr, "__module__", "")
    return module_name and (
        module_name.startswith("sqlalchemy.orm")
        or module_name.startswith("sqlalchemy.sql")
    )


def is_internal_sqlalchemy(attr):
    module_name = getattr(attr, "__module__", "")
    return module_name in {"sqlalchemy.orm.decl_api", "sqlalchemy.sql.schema"}


def skip_sqlalchemy_attribute(attribute):
    return attribute.startswith("_") or attribute in {"registry", "metadata"}


def try_extract_column_type(attr):
    if attr.__class__.__name__ == "InstrumentedAttribute":
        return next(iter(attr.expression.base_columns)).type.python_type
    logging.warning(f"could not extract column type for {attr}")
    return typing.Any


def is_sqlalchemy_orm_model(cls):
    return nested(lambda: str(cls.__class__.__module__), "").startswith(
        "sqlalchemy.orm"
    )


def get_sqlalchemy_init(attributes_with_type):
    res = ["def __init__(self, *,"]
    for p, p_type in attributes_with_type:
        res.append(f"{INDENT}{p}: {p_type} = None,")
    res.append(f"{INDENT}**kw")
    res.append("): ...")
    return res


def is_not_generic_and_private_class_or_module(the_type):
    if type_is_generic(the_type):
        return False
    return getattr(the_type, "__module__", "").startswith("_") or nested(
        lambda: the_type.__class__.__name__, ""
    ).startswith("_")


def get_package(v, attrs):
    pkg_name = attrs.get("__package__") or "%^$%^$%^#"
    if v.startswith(pkg_name):
        return v[len(pkg_name) :]
    return _private_to_public_pkg.get(v, v)


def as_something(k, attrs):
    return f" as {k}" if attrs.get("__file__", "").endswith("__init__.py") else ""


def get_optional_globe(param):
    return (
        "**"
        if param.kind == inspect.Parameter.VAR_KEYWORD
        else "*"
        if param.kind == inspect.Parameter.VAR_POSITIONAL
        else ""
    )

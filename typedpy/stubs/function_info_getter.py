import inspect
import logging

from typedpy.stubs.type_info_getter import (
    get_type_info,
)
from typedpy.stubs.utils import get_optional_globe


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
            else f"{prefix}{get_type_info(annotation, local_attrs, additional_classes)}"
        )
        return _correct_for_return_annotation(res)
    except Exception as e:
        logging.exception(e)
        return ""


def _get_param_by_name(*, sig, local_attrs, additional_classes):
    def _convert_default(d):
        return d.__name__ if inspect.isclass(d) else None

    params_by_name = []
    found_last_positional = False
    for p, v in sig.parameters.items():
        default = (
            "" if v.default == inspect._empty else f" = {_convert_default(v.default)}"
        )
        type_annotation = _get_type_annotation(
            ": ", v.annotation, default, local_attrs, additional_classes
        )
        if v.kind == inspect.Parameter.VAR_POSITIONAL:
            found_last_positional = True
        if v.kind == inspect.Parameter.KEYWORD_ONLY and not found_last_positional:
            params_by_name.append(("*", ""))
            found_last_positional = True
        p_name = f"{get_optional_globe(v)}{p}"
        params_by_name.append((p_name, type_annotation))

    return params_by_name


def get_stubs_of_functions(func_by_name, local_attrs, additional_classes) -> list:
    out_src = []
    for name, func in func_by_name.items():
        sig = inspect.signature(func)
        return_annotations = _get_type_annotation(
            " -> ", sig.return_annotation, "", local_attrs, additional_classes
        )

        params_by_name = _get_param_by_name(
            sig=sig, local_attrs=local_attrs, additional_classes=additional_classes
        )
        params_as_str = ", ".join([f"{k}{v}" for (k, v) in params_by_name])

        out_src.append(f"def {name}({params_as_str}){return_annotations}: ...")
        out_src.append("\n")
    return out_src

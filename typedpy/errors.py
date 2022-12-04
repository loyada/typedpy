import re
import json
from json import JSONDecodeError

from typedpy.structures import ImmutableStructure, Structure
from typedpy.fields import String, AnyOf, Array


class ErrorInfo(ImmutableStructure):
    field = String
    value = String
    problem = AnyOf[String, Array]
    _required = ["problem"]


display_type_by_type = {
    "int": "an integer number",
    "str": "a text value",
    "float": "a decimal number",
    "list": "an array",
}

_expected_class_pattern = re.compile(r"^Expected\s<class '(.*)'>$")


def _transform_class_to_readable(problem: str):
    match = _expected_class_pattern.match(problem)
    if match:
        return f"Expected {display_type_by_type.get(match.group(1), match)}"
    return problem


_pattern_for_typepy_validation_1 = re.compile(r"^([a-zA-Z0-9_.]+): Got ([^;]*); (.*)$")
_pattern_for_typepy_validation_2 = re.compile(r"^([a-zA-Z0-9_.]+):\s(.*); Got (.*)$")
_pattern_for_typepy_validation_3 = re.compile(r"^([a-zA-Z0-9_.]+):\s(.*)$")


def standard_readable_error_for_typedpy_exception(e: Exception, top_level=True):
    err_message = str(e)
    if Structure.failing_fast():
        return _standard_readable_error_for_typedpy_exception_internal(err_message)
    else:
        try:
            errs = json.loads(err_message)
            return [
                _standard_readable_error_for_typedpy_exception_internal(e) for e in errs
            ]
        except JSONDecodeError as ex:
            if not top_level:
                raise ex
            return [
                _standard_readable_error_for_typedpy_exception_internal(err_message)
            ]


def _standard_readable_error_for_typedpy_exception_internal(err_message: str):
    def try_expand(problem_str):
        if not Structure.failing_fast():
            try:
                return standard_readable_error_for_typedpy_exception(
                    Exception(problem_str), top_level=False
                )
            except Exception:
                pass
        return problem_str

    match = _pattern_for_typepy_validation_1.match(err_message)
    if match:
        problem = _transform_class_to_readable(match.group(3))
        return ErrorInfo(
            value=match.group(2), problem=try_expand(problem), field=match.group(1)
        )

    match = _pattern_for_typepy_validation_2.match(err_message)
    if match:
        problem = _transform_class_to_readable(match.group(2))
        return ErrorInfo(
            value=match.group(3), problem=try_expand(problem), field=match.group(1)
        )

    match = _pattern_for_typepy_validation_3.match(err_message)
    if match:
        field = match.group(1)
        problem = _transform_class_to_readable(match.group(2))
        return ErrorInfo(problem=try_expand(problem), field=field)
    return ErrorInfo(problem=err_message)


def get_simplified_error(err: str, as_list=True):
    try:
        res = json.loads(err)
        if isinstance(res, list):
            fixed = []
            for e in res:
                try:
                    key, *rest = e.split(":")
                    val = ":".join(rest)
                    corrected = get_simplified_error(val.strip(), as_list=False)
                    fixed.append(f"{key}: {corrected}")
                except Exception:  # noqa
                    fixed.append(e)

            return fixed if len(res) > 1 or as_list is True else fixed[0]
    except JSONDecodeError:
        pass
    return err

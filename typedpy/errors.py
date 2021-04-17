import re

from typedpy import ImmutableStructure, String


class ErrorInfo(ImmutableStructure):
    field = String
    value = String
    problem = String
    _required = ["problem"]


display_type_by_type = {
    "int": "an integer number",
    "str": "a text value",
    "float": "a decimal number",
    "list": "an array"
}


_expected_class_pattern = re.compile("^Expected\s<class '(.*)'>$")


def _transform_class_to_readable(problem: str):
    match = _expected_class_pattern.match(problem)
    if match:
        return f"Expected {display_type_by_type.get(match.group(1), match)}"
    return problem


_pattern_for_typepy_validation_1 = re.compile("^([a-zA-Z0-9_]+): Got (.*); (.*)$")
_pattern_for_typepy_validation_2 = re.compile("^([a-zA-Z0-9_]+):\s(.*); Got (.*)$")
_pattern_for_typepy_validation_3 = re.compile("^([a-zA-Z0-9_]+):\s(.*)$")


def standard_readable_error_for_typedpy_exception(e: Exception):
    err_message = str(e)
    match = _pattern_for_typepy_validation_1.match(err_message)
    if match:
        return dict(value=match.group(2),
                    problem=_transform_class_to_readable(match.group(3)),
                    field=match.group(1))

    match = _pattern_for_typepy_validation_2.match( err_message)
    if match:
        return dict(value=match.group(3),
                    problem=_transform_class_to_readable(match.group(2)),
                    field= match.group(1))

    match = _pattern_for_typepy_validation_3.match( err_message)
    if match:
        field = match.group(1)
        problem = _transform_class_to_readable(match.group(2))
        return dict(problem=problem, field=field)
    return dict(problem=err_message)

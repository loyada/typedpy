import json
from pathlib import Path
from traceback import extract_stack

import pytest

from typedpy import structure_to_schema, write_code_from_schema


def get_abs_path_from_here(relative_path: str) -> Path:
    """
    return absolute path to file, based on path from the calling location
    :param relative_path: relative path from the loading source file
    :return: absolute path with resolved symlinks
    """
    calling_source_file = extract_stack()[-2].filename
    full_path: Path = Path(calling_source_file).parent / relative_path
    return full_path.resolve()


@pytest.fixture(name="schema_load")
def fixture_schema_load():
    def wrapped(file_name: str) -> dict:
        with open(get_abs_path_from_here(file_name), encoding="utf-8") as f:
            return json.load(f)
    return wrapped

@pytest.fixture(name="code_load")
def fixture_code_load():
    def wrapped(file_name: str) -> str:
        with open(get_abs_path_from_here(file_name), encoding="utf-8") as f:
            return f.read()
    return wrapped


def test_example(schema_load, code_load):
    expected_schema = schema_load("example_schema.json")
    expected_code = code_load("example.py")

    from .example import Example
    schema, definitions = structure_to_schema(Example, {})
    assert definitions == expected_schema["definitions"]
    assert schema == expected_schema["example"]

    write_code_from_schema(schema, definitions, str(get_abs_path_from_here("generated") / "generated_example.py"), "Example")

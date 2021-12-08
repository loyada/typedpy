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
        with open(get_abs_path_from_here("schemas") / file_name, encoding="utf-8") as f:
            return json.load(f)

    return wrapped


@pytest.fixture(name="code_load")
def fixture_code_load():
    def wrapped(file_name: str) -> str:
        with open(get_abs_path_from_here(file_name), encoding="utf-8") as f:
            return f.read()

    return wrapped


@pytest.mark.parametrize("original_class_name, expected_schema_filename, generated_filename",
                         [
                             ("Example1", "example1_schema.json", "generated_example1.py"),
                             ("Example2", "example2_schema.json", "generated_example2.py"),
                             ("Example3", "example3_schema.json", "generated_example3.py")

                         ])
def test_example_code_to_schema_and_back(
        schema_load,
        code_load,
        original_class_name,
        expected_schema_filename,
        generated_filename
):
    expected_schema = schema_load(expected_schema_filename)

    import tests.schema_mapping.structures as original_classes
    # noinspection PyPep8Naming
    OriginalClass = getattr(original_classes, original_class_name)

    schema, definitions = structure_to_schema(OriginalClass, {})
    assert definitions == expected_schema["definitions"]
    assert schema == expected_schema["example"]

    generated_file_name = str(get_abs_path_from_here("generated") / generated_filename)
    expected_file_name = str(get_abs_path_from_here("expected") / generated_filename)

    write_code_from_schema(schema, definitions, generated_file_name, "Example1")
    generated_code = code_load(generated_file_name)
    expected_code = code_load(expected_file_name)
    assert generated_code == expected_code

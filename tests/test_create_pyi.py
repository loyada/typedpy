import dataclasses
import sys
from pathlib import Path
import importlib.util
from typing import Optional

import pytest
from pytest import mark

from typedpy import create_stub_for_file, create_stub_for_file_using_ast, create_pyi
from typedpy.utility import get_abs_path_from_here


def _verify_file_are_same(actual_filename, expected_filename):
    with open(str(actual_filename), encoding="UTF-8") as actual, open(
        str(expected_filename), encoding="UTF-8"
    ) as expected:
        actual_lines = [line for line in actual.readlines() if line.strip()]
        expected_lines = [line for line in expected.readlines() if line.strip()]
        assert len(actual_lines) == len(expected_lines)

        for a, e in zip(actual_lines, expected_lines):
            if a.strip() or e.strip():
                assert a.rstrip() == e.rstrip()


@dataclasses.dataclass
class PYI_TEST_CASE:
    source_path: Path
    reference_path: Path
    additional_properties_default: bool = True
    module_name: Optional[str] = ""


test_cases = [
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/__init__.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/__init__.pyi", __file__
        ),
        module_name="examples",
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/api_example.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/api_example.pyi", __file__
        ),
        module_name="examples.api_example",
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/enums.py", __file__),
        reference_path=get_abs_path_from_here("../.stubs/examples/enums.pyi", __file__),
        module_name="examples.enums",
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/enums2.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/enums2.pyi", __file__
        ),
        module_name="examples.enums2",
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/more_classes.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/more_classes.pyi", __file__
        ),
        module_name="examples.more_classes",
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here(
            "../examples/future_annotations.py", __file__
        ),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/future_annotations.pyi", __file__
        ),
        module_name="examples.future_annotations",
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/generic_stuff.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/generic_stuff.pyi", __file__
        ),
        module_name="examples.generic_stuff",
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/__init__.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/__init__.pyi", __file__
        ),
        module_name="examples",
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/api_example.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/api_example_1.pyi", __file__
        ),
        module_name="examples.api_example",
        additional_properties_default=False,
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/enums.py", __file__),
        reference_path=get_abs_path_from_here("../.stubs/examples/enums.pyi", __file__),
        module_name="examples.enums",
        additional_properties_default=False,
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/enums2.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/enums2.pyi", __file__
        ),
        module_name="examples.enums2",
        additional_properties_default=False,
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/more_classes.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/more_classes_1.pyi", __file__
        ),
        module_name="examples.more_classes",
        additional_properties_default=False,
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here(
            "../examples/future_annotations.py", __file__
        ),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/future_annotations.pyi", __file__
        ),
        module_name="examples.future_annotations",
        additional_properties_default=False,
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/generic_stuff.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/generic_stuff.pyi", __file__
        ),
        module_name="examples.generic_stuff",
        additional_properties_default=False,
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here(
            "../examples/struct_with_constants.py", __file__
        ),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/struct_with_constants_1.pyi", __file__
        ),
        module_name="examples.struct_with_constants",
        additional_properties_default=False,
    ),
]


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
@pytest.mark.parametrize(
    "test_case", test_cases[1:], ids=[str(s.source_path) for s in test_cases[1:]]
)
def test_create_pyi_low_level(test_case: PYI_TEST_CASE):
    spec = importlib.util.spec_from_file_location(
        test_case.module_name, test_case.source_path
    )
    the_module = importlib.util.module_from_spec(spec)
    the_module.__package__ = "examples"
    spec.loader.exec_module(the_module)
    out_dir_name = (
        "stubs_tests_results"
        if test_case.additional_properties_default
        else "stubs_tests_results_1"
    )
    results_dir: Path = get_abs_path_from_here(out_dir_name, __file__)
    pyi_path = (results_dir / f"{test_case.source_path.stem}.pyi").resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    create_pyi(
        str(pyi_path),
        the_module.__dict__,
        additional_properties_default=test_case.additional_properties_default,
    )

    actual_filename = pyi_path

    _verify_file_are_same(actual_filename, str(test_case.reference_path))


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_create_stub_for_file():
    module_name = str(get_abs_path_from_here("../examples/api_example.py", __file__))
    src_root = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(module_name, src_root)
    expected_filename = get_abs_path_from_here(
        "../.stubs/examples/api_example.pyi", __file__
    )
    actual_filename = get_abs_path_from_here("../examples/api_example.pyi", __file__)
    _verify_file_are_same(actual_filename, expected_filename)


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_create_stub_for_sqlalchemy_model():
    module_name = str(get_abs_path_from_here("../examples/models.py", __file__))
    src_root = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file_using_ast(module_name, src_root)
    expected_filename = get_abs_path_from_here(
        "../.stubs/examples/models.pyi", __file__
    )
    actual_filename = get_abs_path_from_here("../examples/models.pyi", __file__)
    _verify_file_are_same(actual_filename, expected_filename)


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_create_stub_for_dataclass():
    module_name = str(get_abs_path_from_here("../examples/some_data.py", __file__))
    src_root = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(module_name, src_root)
    expected_filename = get_abs_path_from_here(
        "../.stubs/examples/some_data.pyi", __file__
    )
    actual_filename = get_abs_path_from_here("../examples/some_data.pyi", __file__)
    _verify_file_are_same(actual_filename, expected_filename)


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
@pytest.mark.parametrize(
    "test_case", test_cases, ids=[str(s.source_path) for s in test_cases]
)
def test_create_stub_for_file_designated_dir(test_case: PYI_TEST_CASE):
    src_root = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(
        str(test_case.source_path),
        src_root,
        str(get_abs_path_from_here("../stubs_for_tests", __file__)),
        additional_properties_default=test_case.additional_properties_default,
    )

    actual_filename = str(
        get_abs_path_from_here(
            f"../stubs_for_tests/examples/{test_case.source_path.stem}.pyi", __file__
        )
    )
    _verify_file_are_same(actual_filename, str(test_case.reference_path))


test_cases_for_subpackage = [
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here(
            "../examples/subpackage/__init__.py", __file__
        ),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/subpackage/__init__.pyi", __file__
        ),
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/subpackage/apis.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/subpackage/apis.pyi", __file__
        ),
    ),
]


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
@pytest.mark.parametrize(
    "test_case",
    test_cases_for_subpackage,
    ids=[str(s.source_path) for s in test_cases_for_subpackage],
)
def test_create_stub_for_file_subpackage(test_case: PYI_TEST_CASE):
    src_root = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(
        str(test_case.source_path),
        src_root,
        str(get_abs_path_from_here("../stubs_for_tests", __file__)),
    )

    actual_filename = str(
        get_abs_path_from_here(
            f"../stubs_for_tests/examples/subpackage/{test_case.source_path.stem}.pyi",
            __file__,
        )
    )
    _verify_file_are_same(actual_filename, str(test_case.reference_path))


test_cases_for_regular_classes = [
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here(
            "../examples/controllers/__init__.py", __file__
        ),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/controllers/__init__.pyi", __file__
        ),
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here(
            "../examples/controllers/another_controller.py", __file__
        ),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/controllers/another_controller.pyi", __file__
        ),
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here(
            "../examples/controllers/job_controller.py", __file__
        ),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/controllers/job_controller.pyi", __file__
        ),
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here(
            "../examples/controllers/Scheduled_controller.py", __file__
        ),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/controllers/Scheduled_controller.pyi", __file__
        ),
    ),
]


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
@pytest.mark.parametrize(
    "test_case",
    test_cases_for_regular_classes,
    ids=[str(s.source_path) for s in test_cases_for_regular_classes],
)
def test_create_stub_for_file_regular_classes(test_case: PYI_TEST_CASE):
    src_root = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(
        str(test_case.source_path),
        src_root,
        str(get_abs_path_from_here("../stubs_for_tests", __file__)),
    )

    actual_filename = str(
        get_abs_path_from_here(
            f"../stubs_for_tests/examples/controllers/{test_case.source_path.stem}.pyi",
            __file__,
        )
    )
    _verify_file_are_same(actual_filename, str(test_case.reference_path))

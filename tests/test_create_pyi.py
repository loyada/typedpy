import dataclasses
import sys
from pathlib import Path
import importlib.util

import pytest
from pytest import mark

from typedpy.type_helpers import create_stub_for_file
from typedpy.utility import get_abs_path_from_here
from typedpy import create_pyi


def _verify_file_are_same(actual_filename, expected_filename):
    with open(str(actual_filename), encoding="UTF-8") as actual, open(
            str(expected_filename), encoding="UTF-8"
    ) as expected:
        for a, e in zip(actual.readlines(), expected.readlines()):
            assert a == e


@dataclasses.dataclass
class PYI_TEST_CASE:
    source_path: Path
    reference_path: Path


test_cases = [
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/api_example.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/api_example.pyi", __file__
        )
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/enums.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/enums.pyi", __file__
        )
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/more_classes.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/more_classes.pyi", __file__
        )
    ),
]


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
@pytest.mark.parametrize("test_case", test_cases, ids=[str(s.source_path) for s in test_cases])
def test_create_pyi_low_level(test_case: PYI_TEST_CASE):
    spec = importlib.util.spec_from_file_location("examples_pyi", test_case.source_path)
    the_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(the_module)

    results_dir: Path = get_abs_path_from_here("stubs_tests_results", __file__)
    pyi_path = (results_dir / f"{test_case.source_path.name}.pyi").resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    create_pyi(str(pyi_path), the_module.__dict__)

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
@pytest.mark.parametrize("test_case", test_cases, ids=[str(s.source_path) for s in test_cases])
def test_create_stub_for_file_designated_dir(test_case: PYI_TEST_CASE):
    src_root = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(
        str(test_case.source_path), src_root, str(get_abs_path_from_here("../stubs_for_tests", __file__))
    )

    actual_filename = str(
        get_abs_path_from_here(f"../stubs_for_tests/examples/{test_case.source_path.stem}.pyi", __file__))
    _verify_file_are_same(actual_filename, str(test_case.reference_path))


test_cases_for_subpackage = [
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/subpackage/__init__.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/subpackage/__init__.pyi", __file__
        )
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/subpackage/apis.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/subpackage/apis.pyi", __file__
        )
    )
]


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
@pytest.mark.parametrize("test_case", test_cases_for_subpackage,
                         ids=[str(s.source_path) for s in test_cases_for_subpackage])
def test_create_stub_for_file_subpackage(test_case: PYI_TEST_CASE):
    src_root = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(
        str(test_case.source_path), src_root, str(get_abs_path_from_here("../stubs_for_tests", __file__))
    )

    actual_filename = str(
        get_abs_path_from_here(f"../stubs_for_tests/examples/subpackage/{test_case.source_path.stem}.pyi", __file__))
    _verify_file_are_same(actual_filename, str(test_case.reference_path))



test_cases_for_regular_classes = [
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/controllers/job_controller.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/controllers/job_controller.pyi", __file__
        )
    ),
    PYI_TEST_CASE(
        source_path=get_abs_path_from_here("../examples/controllers/Scheduled_controller.py", __file__),
        reference_path=get_abs_path_from_here(
            "../.stubs/examples/controllers/Scheduled_controller.pyi", __file__
        )
    )
]


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
@pytest.mark.parametrize("test_case", test_cases_for_regular_classes,
                         ids=[str(s.source_path) for s in test_cases_for_subpackage])
def test_create_stub_for_file_regular_classes(test_case: PYI_TEST_CASE):
    src_root = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(
        str(test_case.source_path), src_root, str(get_abs_path_from_here("../stubs_for_tests", __file__))
    )

    actual_filename = str(
        get_abs_path_from_here(f"../stubs_for_tests/examples/controllers/{test_case.source_path.stem}.pyi", __file__))
    _verify_file_are_same(actual_filename, str(test_case.reference_path))

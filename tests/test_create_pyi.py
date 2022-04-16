import sys
from pathlib import Path
import importlib.util

from pytest import mark

from typedpy.type_helpers import create_stub_for_file
from typedpy.utility import get_abs_path_from_here
from typedpy import create_pyi


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_create_pyi_low_level():
    module_name = str(get_abs_path_from_here("../examples/api_example.py", __file__))
    spec = importlib.util.spec_from_file_location("example_pyi", module_name)
    the_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(the_module)

    full_path: Path = Path(__file__)
    pyi_path = (full_path.parent / "types_for_test_create_pyi").resolve()

    create_pyi(str(pyi_path), the_module.__dict__)

    actual_filename = get_abs_path_from_here("types_for_test_create_pyi.pyi", __file__)
    expected_filename = get_abs_path_from_here(
        "../.stubs/examples/api_example.pyi", __file__
    )
    with open(str(actual_filename), encoding="UTF-8") as actual, open(
        str(expected_filename), encoding="UTF-8"
    ) as expected:
        for a, e in zip(actual.readlines(), expected.readlines()):
            assert a == e


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_create_stub_for_file():
    module_name = str(get_abs_path_from_here("../examples/api_example.py", __file__))
    src_dir = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(module_name, src_dir)


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_create_stub_for_file_designated_dir():
    module_name = str(get_abs_path_from_here("../examples/api_example.py", __file__))
    src_dir = str(get_abs_path_from_here("../", __file__))
    create_stub_for_file(
        module_name, src_dir, str(get_abs_path_from_here("../.stubs", __file__))
    )

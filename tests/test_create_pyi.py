from pathlib import Path

from typedpy import create_pyi
import importlib.util
import filecmp

def get_abs_path_from_here(relative_path: str, calling_file_name: str) -> Path:
    """
    return absolute path to file, based on path from the calling location
    :param calling_file_name: optional name of the calling script that will serce as reference
    :param relative_path: relative path from the loading source file
    :return: absolute path with resolved symlinks
    """
    calling_source_file = calling_file_name
    full_path: Path = Path(calling_source_file).parent / relative_path
    return full_path.resolve()



def test_create_pyi():
    module_name = str(get_abs_path_from_here("api_example.py", __file__))
    spec = importlib.util.spec_from_file_location("example_pyi", module_name)
    the_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(the_module)

    full_path: Path = Path(__file__)
    pyi_path = (full_path.parent / "types_for_test_create_pyi").resolve()

    create_pyi(str(pyi_path), the_module.__dict__)

    actual_filename = get_abs_path_from_here('types_for_test_create_pyi.pyi', __file__)
    expected_filename = get_abs_path_from_here( 'api_example.pyi', __file__)
    assert filecmp.cmp(actual_filename, expected_filename)

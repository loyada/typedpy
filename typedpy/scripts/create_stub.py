import argparse
import fnmatch
from pathlib import Path

from typedpy.type_helpers import create_stub_for_file, create_stub_for_file_using_ast


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src_root_dir", help="source root directory")
    parser.add_argument(
        "src_script_path", help="absolute path of python script to process"
    )
    parser.add_argument(
        "-s",
        "--stubs-dir",
        type=str,
        default=".stubs",
        help="source directory of stubs. Default is .stubs",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        type=str,
        help="exclude patterns in the form path1:path2:path3",
    )
    parser.add_argument('--ast', action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    src_root_abs_path = str(Path(args.src_root_dir).resolve())
    input_file_abs_path = str(Path(args.src_script_path).resolve())
    stub_dir_abs_path = str(Path(src_root_abs_path) / Path(args.stubs_dir))
    use_ast = args.ast

    exclude = args.exclude.split(":") if args.exclude else []
    for x in exclude:
        if fnmatch.fnmatch(input_file_abs_path, x):
            return

    func = create_stub_for_file_using_ast if use_ast else create_stub_for_file
    func(input_file_abs_path, src_root_abs_path, stub_dir_abs_path)


if __name__ == "__main__":
    main()

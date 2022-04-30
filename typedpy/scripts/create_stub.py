import argparse
import fnmatch
import sys
from pathlib import Path

from typedpy.type_helpers import create_stub_for_file


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
    args = parser.parse_args()

    src_root_abs_path = str(Path(args.src_root_dir).resolve())
    input_file_abs_path = str(Path(args.src_script_path).resolve())
    stub_dir_abs_path = str(Path(src_root_abs_path) / Path(args.stubs_dir))

    exclude = args.exclude.split(":") if args.exclude else []
    for x in exclude:
        if fnmatch.fnmatch(input_file_abs_path, x):
            return

    create_stub_for_file(input_file_abs_path, src_root_abs_path, stub_dir_abs_path)


if __name__ == "__main__":
    main()

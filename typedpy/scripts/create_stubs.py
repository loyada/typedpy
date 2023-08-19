import argparse
import fnmatch
import logging
import subprocess
from os import walk
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src_root_dir", help="source root directory")
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
    parser.add_argument("directory", help="directory to process")
    args = parser.parse_args()
    src_root_abs_path = str(Path(args.src_root_dir).resolve())
    input_dir = str(Path(args.directory).resolve())
    stub_dir_abs_path = str(Path(src_root_abs_path) / Path(args.stubs_dir))
    exclude = args.exclude.split(":") if args.exclude else []

    for dirpath, _, filenames in walk(input_dir):
        if dirpath.startswith("__"):
            continue
        _process_dir(dirpath, exclude, filenames, src_root_abs_path, stub_dir_abs_path)


def _process_dir(dirpath, exclude, filenames, src_root_abs_path, stub_dir_abs_path):
    python_scripts = [name for name in filenames if fnmatch.fnmatch(name, "*.py")]
    for name in python_scripts:
        exclude_it = False
        abs_file_path = str(Path(dirpath) / name)
        for x in exclude:
            if fnmatch.fnmatch(abs_file_path, x):
                exclude_it = True
                continue
        if exclude_it:
            continue
        print(f"processing {abs_file_path}")
        try:
            with subprocess.Popen(
                [
                    "create-stub",
                    "-s",
                    stub_dir_abs_path,
                    src_root_abs_path,
                    abs_file_path,
                ],
                stdout=subprocess.PIPE,
            ) as proc:
                res = proc.stdout.read().decode("UTF-8")
                if res:
                    print(res)
            print(f"done with {name}")
        except Exception as e:
            logging.exception(e)


if __name__ == "__main__":
    main()

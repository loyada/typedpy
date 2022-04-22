import fnmatch
import logging
import sys
from os import walk
from pathlib import Path

from typedpy.type_helpers import create_stub_for_file


def main():
    if len(sys.argv)>4 or len(sys.argv)<3:
        print(f"Usage: {sys.argv[0]} <src-root-dir> <directory> [stubs-dir]")
        sys.exit(1)
    src_root_abs_path = str(Path(sys.argv[1]).resolve())
    input_dir = str(Path(sys.argv[2]).resolve())
    stub_dir = sys.argv[3] if len(sys.argv)==4 else ".stubs"
    stub_dir_abs_path = str(Path(src_root_abs_path) / Path(stub_dir))

    for (dirpath, _, filenames) in walk(input_dir):
        if dirpath.startswith("__"):
            continue
        python_scripts = [name for name in filenames if fnmatch.fnmatch(name, '*.py')]
        for name in python_scripts:
            abs_file_path = str(Path(dirpath) / name)
            print(f"processing {abs_file_path}")
            try:
                create_stub_for_file(
                    abs_file_path, src_root_abs_path, stub_dir_abs_path
                )
            except Exception as e:
                logging.exception(e)


if __name__ == "__main__":
    main()

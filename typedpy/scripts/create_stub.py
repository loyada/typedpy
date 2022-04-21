import sys
from pathlib import Path

from typedpy.type_helpers import create_stub_for_file


def main():
    if len(sys.argv)>4 or len(sys.argv)<3:
        print(f"Usage: {sys.argv[0]} <src-root-dir> <src-script-path> [stubs-dir]")
        sys.exit(1)
    src_root_abs_path = str(Path(sys.argv[1]).resolve())
    input_file_abs_path = str(Path(sys.argv[2]).resolve())
    stub_dir = sys.argv[3] if len(sys.argv)==4 else ".stubs"
    src_dir_abs_path = str(Path(src_root_abs_path) / Path(stub_dir))
    create_stub_for_file(
        input_file_abs_path, src_root_abs_path, src_dir_abs_path
    )


if __name__ == "__main__":
    main()

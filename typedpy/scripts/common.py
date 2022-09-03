import argparse


def get_base_parser() -> argparse.ArgumentParser:
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
    return parser

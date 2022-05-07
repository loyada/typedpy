from enum import Enum

from .enums import NamedEnum
from typedpy import create_pyi


class Status(Enum):
    status1 = 1
    status2 = 2
    status3 = 3


class Names(NamedEnum):
    aaa = 1
    bbb = 2
    ccc = 3


if __name__ == "__main__":
    create_pyi(__file__, locals())

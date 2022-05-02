from enum import Enum

from typedpy import create_pyi


class Status(Enum):
    status1 = 1
    status2 = 2
    status3 = 3


if __name__ == "__main__":
    create_pyi(__file__, locals())

import enum

from typedpy import create_pyi


class State(enum.Enum):
    NY = 1
    NJ = 2
    AL = 3
    FL = 4

    @staticmethod
    def by_foo():
        pass

    @classmethod
    def cls_method(cls, i: int) ->int:
       return i if cls else i-1

    @property
    def aaa(self):
        "aaa"

class Sex(enum.Enum):
    male = 1
    female = 2


if __name__ == "__main__":
    create_pyi(__file__, locals())

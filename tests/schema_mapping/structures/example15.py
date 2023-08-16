import enum

from typedpy import Constant, Structure


class Subject(enum.Enum):
    foo = 1
    bar = 2


class Example15(Structure):
    s: Subject = Subject.foo



#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Any, TypeVar, Type, NoReturn
from typedpy import Structure

from dataclasses import dataclass as dataclass
from typing import Optional as Optional
from typing import TypedDict as TypedDict


FROZEN: frozenset = frozenset()

class SomeData:

    a: int
    s: str
    s_opt: Optional[str]

    def __init__(self, a: int, s: str, s_opt: Optional[str]) -> None: ...


class Point2D(dict):

    x: int
    y: int
    label: str


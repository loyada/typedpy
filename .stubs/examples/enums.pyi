
#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn, Iterable
from typedpy import Structure

from enum import Enum
import enum
from typedpy import create_pyi as create_pyi
import enum



class State(Enum):
    NY = enum.auto()
    NJ = enum.auto()
    AL = enum.auto()
    FL = enum.auto()


    
    @staticmethod
    def by_foo(): ...
    
    @classmethod
    def cls_method(cls, i: int) -> int: ...
    
    @property
    def aaa(self): ...


class Sex(Enum):
    male = enum.auto()
    female = enum.auto()




class NamedEnum(Enum):
    pass




#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn
from typedpy import Structure
import enum

from datetime import datetime



class Base:

    base1: int
    base2: list


class JobController(Base):

    base1: int
    CONST_ID: Any
    CONST_ID_WITH_ANNOTATION: str

    def __init__(self, urls: dict[str, dict]): ...

    def execute(self, job_id: str): ...

    def aaa(self, a: list[datetime] = list, o: Optional[str] = None): ...


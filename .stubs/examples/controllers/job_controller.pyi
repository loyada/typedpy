#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn
from typedpy import Structure

from datetime import datetime



class Base:

    base1: int
    base3: dict
    base2: list


class JobController(Base):

    CONST_ID: int
    CONST_ID_WITH_ANNOTATION: str

    def __init__(self, urls: dict[str, dict]): ...

    def execute(self, job_id: str): ...

    def aaa(self, a: list[datetime] = list, o: Optional[str] = None): ...


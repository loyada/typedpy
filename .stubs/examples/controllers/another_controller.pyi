
#### This stub was autogenerated by Typedpy
###########################################

from typing import Union, Optional, Any, TypeVar, Type, NoReturn
from typedpy import Structure

from datetime import datetime as datetime
from datetime import date as date
from .job_controller import JobController as JobController


class AController:

    today: date
    numbers: list[int]
    now: datetime
    _job_controller:  JobController
    value:  int
    _urls:  dict[str, dict] 
    _abc: list
    _name: str
    
    def __init__(self, val: int, other, name: str = None, *, urls: dict[str, dict] = None, job_controller: JobController): ...


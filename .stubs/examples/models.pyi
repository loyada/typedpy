
#### This stub was autogenerated by Typedpy
###########################################

import datetime
from typing import Optional, Any, Iterable, Union
from typedpy import Structure
from sqlalchemy import ForeignKey as ForeignKey
from sqlalchemy import Column as Column
from sqlalchemy import Integer as Integer
from sqlalchemy import String as String
from sqlalchemy.orm import relationship as relationship
from common import Mappable as Mappable
from common import Base as Base
from sqlalchemy import Column



class Customer(Mappable):
    id: Union[Column, int]
    name: Union[Column, str]
    address: Union[Column, str]
    email: Union[Column, str]
    invoices: Any
    foos: Any
    def __init__(self,
            id: int = None,
            name: str = None,
            address: str = None,
            email: str = None,
            invoices = None,
            foos = None,
    ): ...

    @classmethod
    def from_structure(cls,
            structure: Structure,
            *,
            ignore_props: list[str] = None,
            id: int = None,
            name: str = None,
            address: str = None,
            email: str = None,
            invoices = None,
            foos = None,
    ) -> Customer: ...

    @staticmethod
    def by_id(
        session: Session,
        abc,
        *,
        ids: list[int] = None,
        foo: str,
        **kw,
    ) -> dict[int, list[str]]: ...


    def aaa(
        self,
        key,
    ): ...



class Invoice:
    id: Union[Column, int]
    custid: Union[Column, int]
    invno: Union[Column, int]
    amount: Union[Column, int]
    customer: Any
    def __init__(self,
            id: int = None,
            custid: int = None,
            invno: int = None,
            amount: int = None,
            customer = None,
    ): ...


def func(
    session: Session,
    abc,
    *,
    ids: list[int] = None,
    foo: str,
    bar = None,
) -> dict[int, list[str]]: ...



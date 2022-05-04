
#### This stub was autogenerated by Typedpy
###########################################

from typing import Iterable as Iterable
from typedpy import Integer as Integer
from typedpy import String as String
from sqlalchemy import ForeignKey as ForeignKey
from sqlalchemy import Column as Column
from sqlalchemy import Integer as Integer
from sqlalchemy import String as String
from sqlalchemy.orm import relationship as relationship
from common import Mappable as Mappable
from common import Base as Base



class Customer(Mappable):
    id: int
    name: str
    address: str
    email: str
    invoices: Any
    def __init__(self,
            id: int = None,
            name: str = None,
            address: str = None,
            email: str = None,
    ): ...

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
    id: int
    custid: int
    invno: int
    amount: int
    customer: Any
    def __init__(self,
            id: int = None,
            custid: int = None,
            invno: int = None,
            amount: int = None,
    ): ...


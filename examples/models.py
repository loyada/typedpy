from sqlalchemy import ForeignKey, Column, Integer, String
from sqlalchemy.orm import relationship
from common import Mappable, Base


def func(
    session: Session, abc, *, ids: list[int] = None, foo: str, bar=False
) -> dict[int, list[str]]:
    pass


abc = 1


class Column:
    def __init__(self, *args, **kw):
        pass


class Customer(Base, Mappable):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String)
    email = Column(String)
    invoices = relationship("Invoice", back_populates="customer")
    foos = relationship(Foo, back_populates="customer")

    @staticmethod
    def by_id(
        session: Session, abc=5, *, ids: list[int] = [1, 2], foo: str, **kw
    ) -> dict[int, list[str]]:
        pass

    def aaa(self, key):
        pass


class ForeignKey:
    def __init__(self, *args, **kw):
        pass


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    custid = Column(Integer, ForeignKey("customers.id"))
    invno = Column(Integer)
    amount = Column(Integer)
    customer = relationship("Customer", back_populates="invoices")

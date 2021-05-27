from pytest import raises

from typedpy import Structure, DateField, DateTime
from datetime import date, datetime


class Example(Structure):
    the_date = DateField
    the_time = DateTime
    _required = []


def test_datefield_with_datetime():
    assert Example(the_date=datetime.now()).the_date == date.today()


def test_datefield_wrong_type():
    with raises(TypeError):
        Example(the_date=12122020)


def test_date_wrong_type():
    with raises(TypeError):
        Example(the_time=12122020)


def test_datatime():
    e = Example(the_time= datetime.now())
    print(e.the_time)
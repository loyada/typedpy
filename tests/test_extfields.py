from pytest import raises

from typedpy import Structure, DateField, DateTime, deserialize_structure
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
    e = Example(the_time=datetime.now())
    print(e.the_time)


def test_datetime_from_epoch_seconds():
    assert Example(the_time=1700000000).the_time == datetime.fromtimestamp(1700000000)


def test_datetime_from_epoch_seconds_after_2033():
    assert Example(the_time=2100000000).the_time == datetime.fromtimestamp(2100000000)


def test_datetime_from_epoch_milliseconds():
    the_time = Example(the_time=1700000000123).the_time
    assert the_time == datetime.fromtimestamp(1700000000).replace(microsecond=123000)


def test_datetime_from_epoch_milliseconds_before_2001():
    assert Example(the_time=900000000000).the_time == datetime.fromtimestamp(900000000)


def test_datetime_from_int_too_small_for_epoch():
    with raises(TypeError) as excinfo:
        Example(the_time=999999999)
    assert (
        "the_time: Got 999999999; Expected datetime, str, or a Unix timestamp in"
        " seconds or milliseconds" in str(excinfo.value)
    )


def test_datetime_from_epoch_out_of_range():
    with raises(ValueError) as excinfo:
        Example(the_time=10**20)
    assert "the_time: Got 100000000000000000000;" in str(excinfo.value)


def test_datetime_deserialize_epoch():
    assert deserialize_structure(Example, {"the_time": 1700000000123}).the_time == (
        datetime.fromtimestamp(1700000000).replace(microsecond=123000)
    )

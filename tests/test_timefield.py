from datetime import time

import pytest

from typedpy import Deserializer, Serializer, Structure
from typedpy.extfields import TimeField


class Foo(Structure):
    t: TimeField


class Bar(Structure):
    t: time


def test_valid_set():
    now = time()
    assert Foo(t=now).t == now
    assert Foo(t="1:02:00").t == time(hour=1, minute=2)
    assert Bar(t=now).t == now
    assert Bar(t="1:02:00").t == time(hour=1, minute=2)


def test_invalid_set():
    with pytest.raises(TypeError):
        Foo(t=123)

    with pytest.raises(ValueError):
        Foo(t="10-00-00")


def test_deserialization():
    assert Deserializer(Foo).deserialize({"t": "10:01:05"}).t == time(
        hour=10, minute=1, second=5
    )
    assert Deserializer(Bar).deserialize({"t": "10:01:05"}).t == time(
        hour=10, minute=1, second=5
    )


def test_serialization():
    assert Serializer(Foo(t="1:2:00")).serialize() == {"t": "01:02:00"}
    assert Serializer(Bar(t="1:2:00")).serialize() == {"t": "01:02:00"}

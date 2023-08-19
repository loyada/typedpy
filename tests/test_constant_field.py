import enum

import pytest

from typedpy import (
    AbstractStructure,
    Constant,
    Deserializer,
    DoNotSerialize,
    Enum,
    Serializer,
    Structure,
)


class EventSubject(enum.Enum):
    foo = 1
    bar = 2


class Event(AbstractStructure):
    i: int = 5
    subject: Enum[EventSubject]

    _required = ["subject"]


class FooEvent(Event):
    subject = Constant(EventSubject.foo)
    other_subject = Constant(EventSubject.bar)
    name: str
    foo = Constant("fooooo")


class BarEvent(Event):
    subject = Constant(EventSubject.bar)
    val: int


def test_block_invalid_constant():
    with pytest.raises(TypeError) as excinfo:

        class Example(Structure):
            foo = Constant([1, 2, 3])

    assert (
        "Constant foo is of an invalid type. Supported types are : None, int, str, bool, enum.Enum, float"
        in str(excinfo.value)
    )


def test_happy_constant():
    foo_event = FooEvent(name="name")
    assert foo_event.subject is EventSubject.foo
    assert foo_event.other_subject is EventSubject.bar
    assert foo_event.foo == "fooooo"
    assert BarEvent(val=5).subject is EventSubject.bar


def test_not_allowed_to_set():
    with pytest.raises(ValueError) as excinfo:
        FooEvent(name="name", subject=EventSubject.bar)
    assert "FooEvent:  subject is defined as a constant. It cannot be set." in str(
        excinfo.value
    )


def test_not_allowed_to_updated():
    foo = FooEvent(name="name")
    with pytest.raises(ValueError) as excinfo:
        foo.subject = EventSubject.bar
    assert "FooEvent:  subject is defined as a constant. It cannot be set." in str(
        excinfo.value
    )


def test_not_allowed_to_inheritance():
    class FooChild(FooEvent):
        s: str

    foo = FooChild(name="name", s="abc")
    assert foo.subject is EventSubject.foo

    with pytest.raises(ValueError) as excinfo:
        foo.subject = EventSubject.bar
    assert "FooChild:  subject is defined as a constant. It cannot be set." in str(
        excinfo.value
    )

    with pytest.raises(ValueError) as excinfo:
        FooChild(name="name", subject=EventSubject.bar, s="abc")
    assert "FooChild:  subject is defined as a constant. It cannot be set." in str(
        excinfo.value
    )


def test_serialization():
    foo = FooEvent(name="name", i=3)
    assert Serializer(foo).serialize() == {
        "name": "name",
        "subject": "foo",
        "i": 3,
        "other_subject": "bar",
        "foo": "fooooo",
    }


def test_deserialization():
    assert Deserializer(FooEvent).deserialize(
        {"name": "name", "subject": "foo", "i": 3}
    ) == FooEvent(name="name", i=3)
    assert Deserializer(FooEvent).deserialize(
        {
            "name": "name",
            "subject": "foo",
            "i": 3,
            "other_subject": "bar",
            "foo": "fooooo",
        }
    ) == FooEvent(name="name", i=3)
    # it actually ignores the values in constant fields:
    assert Deserializer(FooEvent).deserialize(
        {"name": "name", "subject": "x", "i": 3}
    ) == FooEvent(name="name", i=3)


def test_shallow_clone():
    foo = FooEvent(name="name")
    with pytest.raises(ValueError) as excinfo:
        foo.shallow_clone_with_overrides(subject=EventSubject.bar)
    assert "FooEvent:  subject is defined as a constant. It cannot be set." in str(
        excinfo.value
    )
    assert foo.shallow_clone_with_overrides().subject is EventSubject.foo


def test_from_other_class():
    foo = FooEvent(name="name")
    with pytest.raises(ValueError) as excinfo:
        foo.shallow_clone_with_overrides(subject=EventSubject.bar)
    assert "FooEvent:  subject is defined as a constant. It cannot be set." in str(
        excinfo.value
    )
    assert foo.shallow_clone_with_overrides().subject is EventSubject.foo


def test_from_other_class():
    foo = FooEvent(name="name")
    with pytest.raises(ValueError) as excinfo:
        FooEvent.from_other_class(foo, subject=EventSubject.bar)
    assert "FooEvent:  subject is defined as a constant. It cannot be set." in str(
        excinfo.value
    )
    assert FooEvent.from_other_class(foo).subject is EventSubject.foo


def test_mapper_can_be_empty():
    class FooBase(Structure):
        i: int

    class Foo(FooBase):
        const1 = Constant(1)
        const2 = Constant(2)

    _serialization_mapper = {"const1": DoNotSerialize, "const2": DoNotSerialize}

    foo = Deserializer(Foo).deserialize({"i": 5})
    assert foo.i == 5
    assert foo.const2 == 2

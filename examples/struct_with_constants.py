import enum


from typedpy import AbstractStructure, Constant, Enum


class EventSubject(enum.Enum):
    foo = 1
    bar = 2


class Event(AbstractStructure):
    i: int = 5
    subject: Enum[EventSubject]

    _required = ["subject"]


class FooEvent(Event):
    subject = Constant(EventSubject.foo)
    name: str


class BarEvent(Event):
    subject = Constant(EventSubject.bar)
    val: int

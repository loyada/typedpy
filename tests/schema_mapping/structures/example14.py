import enum


from typedpy import AbstractStructure, Constant, Enum


class EventSubject(enum.Enum):
    foo = 1
    bar = 2


class Event(AbstractStructure):
    i: int = 5
    subject: EventSubject

    _required = ["subject"]


class Example14(Event):
    subject = Constant(EventSubject.foo)
    other_subject = Constant(EventSubject.bar)
    name: str
    other = Constant("example")

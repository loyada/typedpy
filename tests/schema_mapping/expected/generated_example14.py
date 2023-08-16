from typedpy import *


class Example1(Structure):
    i: Integer(default=5)
    subject: Enum(values=['foo'])
    other_subject: Enum(values=['bar'])
    other: Enum(values=['example'])
    name: String()

    _required = ['name', 'other', 'other_subject', 'subject']

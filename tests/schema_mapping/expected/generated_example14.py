from typedpy import *


class Example1(Structure):
    i = Integer(default=5)
    subject = Enum(values=['foo', 'bar'])
    name = String()

    _required = ['name', 'subject']

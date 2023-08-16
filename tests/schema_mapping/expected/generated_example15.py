from typedpy import *


class Example1(Structure):
    s: Enum(values=['foo', 'bar'], default='foo')

    _required = []


from typedpy import *


class Example1(Structure):
    D = Map(items=[String(), Integer()], default=lambda: {'abc': 0})

    _required = []

from typedpy import *


class Example1(Structure):
    D = Map(items=[String(), Integer()], default=lambda: {'abc': 0})
    I = Integer()
    S = Array(uniqueItems=True)
    X = Integer()

    _required = ['I', 'S', 'X']

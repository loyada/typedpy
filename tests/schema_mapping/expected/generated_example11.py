from typedpy import *


class Example1(Structure):
    many: Array(items=Enum(values=[1, 2, 3]))
    i: Integer()

    _required = ['i', 'many']

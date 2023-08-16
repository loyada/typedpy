from typedpy import *


class Example1(Structure):
    bbCc: Integer()
    x: String()

    _required = ['bbCc', 'x']

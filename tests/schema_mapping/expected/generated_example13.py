from typedpy import *


class Example1(Structure):
    ip = IPV4()
    as_of = DateField()
    i = Integer(minimum=5)

    _required = []

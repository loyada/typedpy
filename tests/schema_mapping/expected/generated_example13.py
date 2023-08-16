from typedpy import *


class Example1(Structure):
    _additional_properties = False
    ip: IPV4()
    as_of: DateField()
    i: Integer(minimum=5)
    f: Number()

    _required = []

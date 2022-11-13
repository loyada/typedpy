from datetime import date

from typedpy import IPV4, Integer, Structure


class Example13(Structure):
    ip: IPV4
    as_of: date
    i: Integer(minimum=5)

    _required = []
    _additional_properties = False

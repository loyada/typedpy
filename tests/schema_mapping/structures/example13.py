from typedpy import DateField, IPV4, Integer, Structure


class Example13(Structure):
    ip: IPV4
    as_of: DateField
    i: Integer(minimum=5)

    _required = []

from pytest import raises

from typedpy import Structure, Number, String, Integer, Map


class Example(Structure):
    _required = []
    a = Map(minItems= 3, maxItems= 5, items = [Number(maximum=10), String()])
    b = Map(items = [Number(maximum=10), String])
    c = Map(minItems= 3, maxItems= 5)
    d = Map[String(minLength=3), Number()]
    e = Map[String, Number]




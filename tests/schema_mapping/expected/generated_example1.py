from typedpy import *


class Foo(Structure):
    s = String()

    _required = ['s']

# ********************


class Example1(Structure):
    c = OneOf(fields=[Number(multiplesOf=5, minimum=-10, maximum=20), Integer(), Number(minimum=1e-06), String()])
    d = NotField(fields=[Number(multiplesOf=5, minimum=-10, maximum=20), String()])
    e = AllOf(fields=[])
    broken = AllOf(fields=[String(), Integer()])
    f = NotField(fields=[Number()])
    g = AnyOf(fields=[Foo, Integer()])
    a = AllOf(fields=[Number(multiplesOf=5, minimum=-10, maximum=20), Integer(), Number(minimum=1e-06)])
    b = AnyOf(fields=[Number(minimum=-10, maximum=20), Integer(), Number(minimum=1e-06), String()])
    values = Enum(values=['one', 'two', 'three'])
    m = Map(items=[String(), Foo])

    _required = []

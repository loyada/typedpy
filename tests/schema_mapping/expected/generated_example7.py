from typedpy import *


class Foo(Structure):
    xyz = Array()
    j = Integer()

    _required = ['j', 'xyz']

# ********************


class Example1(Structure):
    XYZ = Array()
    J = Integer()
    A = Array()
    S = String()
    FOO = Foo

    _required = ['A', 'FOO', 'J', 'S', 'XYZ']

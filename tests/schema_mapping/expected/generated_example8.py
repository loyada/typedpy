from typedpy import *


class Foo(Structure):
    xyz: Array()
    j: Integer()

    _required = ['j', 'xyz']

# ********************


class Example1(Structure):
    xyz: Array()
    j: Integer()
    a: Array()
    s: String()
    foo: Foo

    _required = ['a', 'foo', 'j', 's', 'xyz']
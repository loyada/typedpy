from typedpy import *


class SimpleStruct(Structure):
    name: String(maxLength=8, pattern='[A-Za-z]+$')

    _required = ['name']


class ComplexStruct(Structure):
    simple: SimpleStruct

    _required = ['simple']

# ********************


class Example1(Structure):
    foo: StructureReference(_required=['a1', 'a2'], a2=Number(), a1=Integer())
    ss: ComplexStruct
    enum: Enum(values=[1, 2, 3])
    s: String(maxLength=5)
    i: Integer(maximum=10)
    all: AllOf(fields=[Number(), Integer()])
    a: Array(items=[Integer(multiplesOf=5), Number()])

    _required = ['a', 'all', 'enum', 'foo', 'i', 's', 'ss']

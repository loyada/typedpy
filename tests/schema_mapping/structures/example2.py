from typedpy import *


class SimpleStruct(Structure):
    name: String(maxLength=8, pattern="[A-Za-z]+$")


class ComplexStruct(ImmutableStructure):
    simple: SimpleStruct


# ********************


class Example2(Structure):
    """
    This is a test of schema mapping
    """

    foo = StructureReference(_required=["a2", "a1"], a2=Float(), a1=Integer())
    ss = ComplexStruct
    enum = Enum(values=[1, 2, 3])
    s = String(maxLength=5)
    i = Integer(maximum=10)
    all = AllOf[Number, Integer]
    a = Array(items=[Integer(multiplesOf=5), Number])

    _required = ["foo", "ss", "enum", "s", "i", "all", "a"]

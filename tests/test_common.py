from typing import List


from typedpy import Integer, String, Structure, StructureReference
from typedpy.commons import deep_get, nested, Undefined


def test_deep_get():
    assert deep_get({"a1": {"b": {"c": 5}}, "a2": 2}, "a1.b.c") == 5
    assert deep_get({"a1": {"b": {"c": 5}}, "a2": 2}, "a2") == 2
    assert deep_get({"a1": {"b": {"c": 5}}, "a2": 2}, "a1.x") is None
    assert deep_get({}, "x.y") is None
    assert deep_get({}, "x.y", enable_undefined=True) is Undefined

def test_nested_list():
    class Bar(Structure):
        x = StructureReference(i=Integer(), s=String())

    class Foo(Structure):
        a: List[Bar]

        _additionalProperties = False

    foo = Foo(a=[Bar(x={"i": 5, "s": "xyz"})])
    assert nested(lambda: foo.a[1].x.i) is None
    assert nested(lambda: foo.a[1].x.i, default=1) == 1
    assert nested(lambda: foo.a[0].x.i) == 5
    assert nested(lambda: foo.a[0].x.w) is None

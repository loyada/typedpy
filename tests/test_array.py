import copy
import sys

import pytest
from pytest import raises

from typedpy import Structure, Array, Number, String, Integer, Field, ImmutableStructure


class Foo(Structure):
    s = String


class Example(Structure):
    _additionalProperties = True
    _required = []
    # array support, similar to json schema
    a = Array(uniqueItems=True, minItems=3, items=[String(), Number(maximum=10)])
    b = Array(minItems=3, maxItems=5, items=Number(maximum=10))
    c = Array(items=[String(), String(), Number(maximum=10)])
    d = Array(minItems=2, items="")
    e = Array(minItems=2)
    f = Array[Integer]
    g = Array[Foo]
    h = Array[Array[Integer]]


def test_wrong_type_for_array_err():
    with raises(TypeError) as excinfo:
        Example(a=2)
    assert "a: Got 2; Expected <class 'list'>" in str(excinfo.value)


def test_wrong_type_for_array_items_err():
    with raises(TypeError) as excinfo:
        Example(a=["aa", [], 2])
    assert "a_1: Got []; Expected a number" in str(excinfo.value)


def test_non_unique_items_err():
    with raises(ValueError) as excinfo:
        Example(a=["aa", 2, 2])
    assert "a: Got ['aa', 2, 2]; Expected unique items" in str(excinfo.value)


def test_invalid_number_in_array_err():
    with raises(ValueError) as excinfo:
        Example(a=["aa", 12, 2])
    assert "a_1: Got 12; Expected a maximum of 10" in str(excinfo.value)


def test_invalid_number_in_array_variation_err():
    t = Example(a=["aa", 5, 2])
    with raises(ValueError) as excinfo:
        t.a[1] += 9
    assert "a_1: Got 14; Expected a maximum of 10" in str(excinfo.value)


def test_no_schema_for_item_so_no_validation():
    t = Example(a=["aa", 5, 2])
    t.a[2] = None
    assert t.a == ["aa", 5, None]


def test_a_is_valid():
    Example(a=["aa", 5, 2])


def test_update_1():
    t = Example(a=["aa", 5, 2])
    t.a[2] += 6
    assert t.a == ["aa", 5, 8]
    assert t.a[2] == 8


def test_update_append():
    t = Example(a=["aa", 5, 2])
    t.a.append(6)
    assert t.a == ["aa", 5, 2, 6]


def test_append_maintains_field_definition():
    t = Example(a=["aa", 5, 2])
    t.a.append(6)
    with raises(TypeError) as excinfo:
        t.a[0] = 0
    assert "a_0: Got 0; Expected a string" in str(excinfo.value)


def test_append_maintains_field_definition_validate_pop():
    t = Example(a=["aa", 5, 2])
    t.a.append(6)
    with raises(TypeError) as excinfo:
        t.a.pop(0)
    assert "a_0: Got 5; Expected a string" in str(excinfo.value)


def test_update_too_short_err():
    t = Example(a=["aa", 5, 2])
    with raises(ValueError) as excinfo:
        t.a = [""]
    assert "a: Expected length of at least 3" in str(excinfo.value)


def test_update_to_wrong_type_err():
    t = Example(a=["aa", 5, 2])
    with raises(TypeError) as excinfo:
        t.a[0] = 1
    assert "a_0: Got 1; Expected a string" in str(excinfo.value)


def test_not_enough_items_err():
    with raises(ValueError) as excinfo:
        Example(a=["aa", 2])
    assert "a: Expected length of at least 3" in str(excinfo.value)


def test_too_many_items_err():
    with raises(ValueError) as excinfo:
        Example(b=[1, 2, 3, 4, 5, 6])
    assert "b: Expected length of at most 5" in str(excinfo.value)


def test_single_field_for_all_items_err():
    with raises(ValueError) as excinfo:
        Example(b=[1, 2, 3, 99])
    assert "b_3: Got 99; Expected a maximum of 10" in str(excinfo.value)


def test_single_field_for_all_items_valid():
    t = Example(b=[1, 2, 3, 9])
    assert t.b == [1, 2, 3, 9]


def test_not_enough_items2_err():
    with raises(ValueError) as excinfo:
        Example(c=["aa"])
    assert "c: Got ['aa']; Expected an array of length 3" in str(excinfo.value)


def test_items_can_be_ignored_schema_is_valid():
    assert Example(d=[1, 2, 3]).d[1] == 2


def test_no_items_schema_is_valid():
    assert Example(e=[1, 2, 3]).e[1] == 2


def test_generics_version_err():
    with raises(ValueError) as excinfo:
        Example(f=["aa", "xx"])
    assert "f: f_0: Expected <class 'int'>" in str(excinfo.value)


def test_generics_version_err():
    assert Example(f=[4, 5, 6]).f == [4, 5, 6]


def test_extend_err():
    e = Example(b=[1, 2, 3])
    with raises(ValueError) as excinfo:
        e.b.extend([5, 99])
    assert "b_4: Got 99; Expected a maximum of 10" in str(excinfo.value)


def test_extend_valid():
    from typedpy.fields import _ListStruct

    e = Example(b=[1, 2, 3])
    e.b.extend([5, 9])
    assert e.b == [1, 2, 3, 5, 9]
    assert e.b.__class__ == _ListStruct


def test_extend_maintains_field_definition():
    e = Example(b=[1, 2, 3])
    e.b.extend([5, 9])
    with raises(TypeError) as excinfo:
        e.b[0] = "xxx"
    assert "b_0: Got 'xxx'; Expected a number" in str(excinfo.value)


def test_insert_err():
    e = Example(b=[1, 2, 3])
    with raises(TypeError) as excinfo:
        e.b.insert(2, "a")
    assert "b_2: Got 'a'; Expected a number" in str(excinfo.value)


def test_insert_valid():
    e = Example(b=[1, 2, 3])
    e.b.insert(1, 9)
    assert e.b == [1, 9, 2, 3]


def test_remove_err():
    e = Example(b=[1, 2, 3])
    with raises(ValueError) as excinfo:
        e.b.remove(2)
    assert "b: Expected length of at least 3" in str(excinfo.value)


def test_remove_valid():
    e = Example(b=[1, 2, 3, 4])
    e.b.remove(1)
    assert e.b == [2, 3, 4]


def test_pop_err():
    e = Example(b=[1, 2, 3])
    with raises(ValueError) as excinfo:
        e.b.pop()
    assert "b: Expected length of at least 3" in str(excinfo.value)


def test_pop_valid():
    e = Example(b=[1, 2, 3, 4])
    e.b.pop()
    assert e.b == [1, 2, 3]


def test_array_of_defined_structure_type_err():
    with raises(TypeError) as excinfo:
        Example(g=[Foo(s="abc"), 4])
    assert "g_1: Expected <Structure: Foo. Properties: s = <String>>" in str(
        excinfo.value
    )


def test_array_of_defined_structure_valid():
    assert Example(g=[Foo(s="abc"), Foo(s="def")]).g[1].s == "def"


def test_array_of_array_type_err1():
    with raises(TypeError) as excinfo:
        Example(h=[3, 4])
    assert "h_0: Got 3; Expected <class 'list'>" in str(excinfo.value)


def test_array_of_array_type_err2():
    with raises(TypeError) as excinfo:
        Example(h=[[1, 2], ["aaa", "ccc"]])
    assert "h_1_0: Expected <class 'int'>" in str(excinfo.value)


def test_array_of_array_valid():
    assert Example(h=[[1, 2], [3, 4]]).h[1] == [3, 4]


def test_class_reference_err1():
    class Bar(Structure):
        st = String

    class Foo(Structure):
        bars = Array(items=Bar)

    with raises(TypeError) as excinfo:
        Foo(bars=[1])
    assert "bars_0: Expected <Structure: Bar. Properties: st = <String>>" in str(
        excinfo.value
    )


def test_class_reference_err2():
    class Bar(Structure):
        st = String

    class Foo(Structure):
        bars = Array(items=[Bar, Bar])

    with raises(TypeError) as excinfo:
        Foo(bars=[Bar(st="a"), 1])
    assert "bars_1: Expected <Structure: Bar. Properties: st = <String>>" in str(
        excinfo.value
    )


def test_class_reference_success():
    class Bar(Structure):
        st = String

    class Foo(Structure):
        bars = Array(items=Bar)

    foo = Foo(bars=[Bar(st="a"), Bar(st="b")])
    assert foo.bars[1].st == "b"


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.6 or higher")
def test_array_with_function_returning_field():
    def MyField() -> Field:
        return String()

    class Foo(Structure):
        a = Array[MyField]
        s = String

    assert Foo(a=["xyz"], s="abc").a[0] == "xyz"


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.6 or higher")
def test_array_with_function_returning_field_with_params():
    def MyField(i) -> Field:
        return String(minLength=1)

    with raises(TypeError) as excinfo:

        class Foo(Structure):
            a = Array[MyField]
            s = String

    assert "Unsupported field type in definition" in str(excinfo.value)


def test_copy():
    class Foo(ImmutableStructure):
        a = Array

    foo = Foo(a=[1, 2, 3])
    b = foo.a.copy()
    b.append(4)
    assert 4 not in foo.a


def test_clear_error_if_immutable():
    class Foo(ImmutableStructure):
        a = Array

    foo = Foo(a=[1, 2, 3])
    with raises(ValueError):
        foo.a.clear()


def test_clear_for_array_with_minimal_size():
    class Foo(Structure):
        a = Array(minItems=3)

    foo = Foo(a=[1, 2, 3])
    with raises(ValueError) as excinfo:
        foo.a.clear()
    assert "a: Expected length of at least 3; Got []" in str(excinfo.value)


def test_clear():
    class Foo(Structure):
        a = Array

    foo = Foo(a=[1, 2, 3])
    foo.a.clear()
    assert len(foo.a) == 0


def test_deep_copy_array():
    class Foo(Structure):
        a = Array[Integer, Integer, String]

    foo = Foo(a=[1, 2, "x"])
    assert copy.deepcopy(foo) == foo

import sys
from collections import deque

import pytest
from pytest import raises

from typedpy import Structure, Deque, Number, String, Integer, Field, ImmutableStructure, ImmutableDeque
from typedpy.fields import _DequeStruct

class Foo(Structure):
    s = String


class Example(Structure):
    _additionalProperties = True
    _required = []
    # deque support, similar to json schema
    a = Deque(uniqueItems=True, minItems=3, items=[String(), Number(maximum=10)])
    b = Deque(minItems=3, maxItems=5, items=Number(maximum=10))
    c = Deque(items=[String(), String(), Number(maximum=10)])
    d = Deque(minItems=2, items="")
    e = Deque(minItems=2)
    f = Deque[Integer]
    g = Deque[Foo]
    h = Deque[Deque[Integer]]
    i = ImmutableDeque[String]


def test_wrong_type_for_deque_err():
    with raises(TypeError) as excinfo:
        Example(a=2)
    assert "a: Got 2; Expected <class 'collections.deque'>" in str(excinfo.value)


def test_wrong_type_for_deque_items_err():
    with raises(TypeError) as excinfo:
        Example(a=deque(["aa", [], 2]))
    assert "a_1: Got []; Expected a number" in str(excinfo.value)


def test_non_unique_items_err():
    with raises(ValueError) as excinfo:
        Example(a=deque(["aa", 2, 2]))
    assert "a: Got deque(['aa', 2, 2]); Expected unique items" in str(excinfo.value)


def test_invalid_number_in_deque_err():
    with raises(ValueError) as excinfo:
        Example(a=deque(["aa", 12, 2]))
    assert "a_1: Got 12; Expected a maximum of 10" in str(excinfo.value)


def test_invalid_number_in_deque_variation_err():
    t = Example(a=deque(["aa", 5, 2]))
    with raises(ValueError) as excinfo:
        t.a[1] += 9
    assert "a_1: Got 14; Expected a maximum of 10" in str(excinfo.value)


def test_no_schema_for_item_so_no_validation():
    t = Example(a=deque(["aa", 5, 2]))
    t.a[2] = None
    assert t.a == deque(["aa", 5, None])


def test_a_is_valid():
    Example(a=deque(["aa", 5, 2]))


def test_update_1():
    t = Example(a=deque(["aa", 5, 2]))
    t.a[2] += 6
    assert t.a == deque(["aa", 5, 8])
    assert t.a[2] == 8


def test_rotate():
    example = Example(b=deque([1, 2, 3, 4, 5]))
    example.b.rotate(1)
    assert example.b.popleft() == 5


def test_reverse():
    example = Example(b=deque([1, 2, 3, 4, 5]))
    example.b.reverse()
    assert example.b.popleft() == 5
    assert example.b.pop() == 1


def test_update_append():
    t = Example(a=deque(["aa", 5, 2]))
    t.a.append(6)
    assert t.a == deque(["aa", 5, 2, 6])


def test_update_appendleft():
    t = Example(b=deque([1, 5, 2]))
    t.b.appendleft(6)
    assert t.b == deque([6, 1, 5, 2])


def test_append_maintains_field_definition():
    t = Example(a=deque(["aa", 5, 2]))
    t.a.append(6)
    with raises(TypeError) as excinfo:
        t.a[0] = 0
    assert "a_0: Got 0; Expected a string" in str(excinfo.value)
    with raises(ValueError) as excinfo:
        t.a.appendleft(6)
    assert "a: Got deque([6, 'aa', 5, 2, 6]); Expected unique items" in str(
        excinfo.value
    )


def test_append_maintains_field_definition_validate_pop():
    t = Example(a=deque(["aa", 5, 2]))
    t.a.append(6)
    with raises(TypeError) as excinfo:
        t.a.popleft()
    assert "a_0: Got 5; Expected a string" in str(excinfo.value)


def test_update_too_short_err():
    t = Example(a=deque(["aa", 5, 2]))
    with raises(ValueError) as excinfo:
        t.a = deque([""])
    assert "a: Expected length of at least 3" in str(excinfo.value)


def test_update_to_wrong_type_err():
    t = Example(a=deque(["aa", 5, 2]))
    with raises(TypeError) as excinfo:
        t.a[0] = 1
    assert "a_0: Got 1; Expected a string" in str(excinfo.value)


def test_not_enough_items_err():
    with raises(ValueError) as excinfo:
        Example(a=deque(["aa", 2]))
    assert "a: Expected length of at least 3" in str(excinfo.value)


def test_too_many_items_err():
    with raises(ValueError) as excinfo:
        Example(b=deque([1, 2, 3, 4, 5, 6]))
    assert "b: Expected length of at most 5" in str(excinfo.value)


def test_single_field_for_all_items_err():
    with raises(ValueError) as excinfo:
        Example(b=deque([1, 2, 3, 99]))
    assert "b_3: Got 99; Expected a maximum of 10" in str(excinfo.value)


def test_single_field_for_all_items_valid():
    t = Example(b=deque([1, 2, 3, 9]))
    assert t.b == deque([1, 2, 3, 9])


def test_not_enough_items2_err():
    with raises(ValueError) as excinfo:
        Example(c=deque(["aa"]))
    assert "c: Got deque(['aa']); Expected an deque of length 3" in str(excinfo.value)


def test_items_can_be_ignored_schema_is_valid():
    assert Example(d=deque([1, 2, 3])).d[1] == 2


def test_no_items_schema_is_valid():
    assert Example(e=deque([1, 2, 3])).e[1] == 2


def test_generics_version_err():
    with raises(ValueError) as excinfo:
        Example(f=deque(["aa", "xx"]))
    assert "f: f_0: Expected <class 'int'>" in str(excinfo.value)


def test_generics_version_err():
    assert Example(f=deque([4, 5, 6])).f == deque([4, 5, 6])


def test_extend_err():
    e = Example(b=deque([1, 2, 3]))
    with raises(ValueError) as excinfo:
        e.b.extend([5, 99])
    assert "b_4: Got 99; Expected a maximum of 10" in str(excinfo.value)

    with raises(ValueError) as excinfo:
        e.b.extendleft([5, 99])
    assert "b_0: Got 99; Expected a maximum of 10" in str(excinfo.value)


def test_extend_valid():
    from typedpy.fields import _ListStruct

    e = Example(b=deque([1, 2, 3]))
    e.b.extend([5, 9])
    assert list(e.b) == [1, 2, 3, 5, 9]
    assert e.b.__class__ == _DequeStruct

    e = Example(b=deque([1, 2, 3]))
    e.b.extendleft([5, 9])
    assert list(e.b) == [9, 5, 1, 2, 3]
    assert e.b.__class__ == _DequeStruct


def test_extend_maintains_field_definition():
    e = Example(b=deque([1, 2, 3]))
    e.b.extend([5, 9])
    with raises(TypeError) as excinfo:
        e.b[0] = "xxx"
    assert "b_0: Got 'xxx'; Expected a number" in str(excinfo.value)


def test_insert_err():
    e = Example(b=deque([1, 2, 3]))
    with raises(TypeError) as excinfo:
        e.b.insert(2, "a")
    assert "b_2: Got 'a'; Expected a number" in str(excinfo.value)


def test_insert_valid():
    e = Example(b=deque([1, 2, 3]))
    e.b.insert(1, 9)
    assert list(e.b) == [1, 9, 2, 3]


def test_remove_err():
    e = Example(b=deque([1, 2, 3]))
    with raises(ValueError) as excinfo:
        e.b.remove(2)
    assert "b: Expected length of at least 3" in str(excinfo.value)


def test_remove_valid():
    e = Example(b=deque([1, 2, 3, 4]))
    e.b.remove(1)
    assert list(e.b) == [2, 3, 4]


def test_pop_err():
    e = Example(b=deque([1, 2, 3]))
    with raises(ValueError) as excinfo:
        e.b.pop()
    assert "b: Expected length of at least 3" in str(excinfo.value)


def test_pop_valid():
    e = Example(b=deque([1, 2, 3, 4]))
    e.b.pop()
    assert list(e.b) == [1, 2, 3]


def test_deque_of_defined_structure_type_err():
    with raises(TypeError) as excinfo:
        Example(g=deque([Foo(s="abc"), 4]))
    assert "g_1: Expected <Structure: Foo. Properties: s = <String>>" in str(
        excinfo.value
    )


def test_deque_of_defined_structure_valid():
    assert Example(g=deque([Foo(s="abc"), Foo(s="def")])).g[1].s == "def"


def test_deque_of_deque_type_err1():
    with raises(TypeError) as excinfo:
        Example(h=deque([3, 4]))
    assert "h_0: Got 3; Expected <class 'collections.deque'>" in str(excinfo.value)


def test_deque_of_deque_type_err2():
    with raises(TypeError) as excinfo:
        Example(h=deque([deque([1, 2]), deque(["aaa", "ccc"])]))
    assert "h_1_0: Expected <class 'int'>" in str(excinfo.value)


def test_deque_of_deque_valid():
    assert Example(h=deque([deque([1, 2]), deque([3, 4])])).h[1] == deque([3, 4])


def test_class_reference_err1():
    class Bar(Structure):
        st = String

    class Foo(Structure):
        bars = Deque(items=Bar)

    with raises(TypeError) as excinfo:
        Foo(bars=deque([1]))
    assert "bars_0: Expected <Structure: Bar. Properties: st = <String>>" in str(
        excinfo.value
    )


def test_class_reference_err2():
    class Bar(Structure):
        st = String

    class Foo(Structure):
        bars = Deque(items=[Bar, Bar])

    with raises(TypeError) as excinfo:
        Foo(bars=deque([Bar(st="a"), 1]))
    assert "bars_1: Expected <Structure: Bar. Properties: st = <String>>" in str(
        excinfo.value
    )


def test_class_reference_success():
    class Bar(Structure):
        st = String

    class Foo(Structure):
        bars = Deque(items=Bar)

    foo = Foo(bars=deque([Bar(st="a"), Bar(st="b")]))
    assert foo.bars[1].st == "b"


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.6 or higher")
def test_deque_with_function_returning_field():
    def MyField() -> Field:
        return String()

    class Foo(Structure):
        a = Deque[MyField]
        s = String

    assert Foo(a=deque(["xyz"]), s="abc").a[0] == "xyz"


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.6 or higher")
def test_deque_with_function_returning_field_with_params():
    def MyField(i) -> Field:
        return String(minLength=1)

    with raises(TypeError) as excinfo:

        class Foo(Structure):
            a = Deque[MyField]
            s = String

    assert "Unsupported field type in definition" in str(excinfo.value)


def test_copy():
    class Foo(ImmutableStructure):
        a = Deque

    foo = Foo(a=deque([1, 2, 3]))
    b = foo.a.copy()
    b.append(4)
    assert 4 not in foo.a


def test_clear_error_if_immutable():
    class Foo(ImmutableStructure):
        a = Deque

    foo = Foo(a=deque([1, 2, 3]))
    with raises(ValueError):
        foo.a.clear()


def test_clear_for_deque_with_minimal_size():
    class Foo(Structure):
        a = Deque(minItems=3)

    foo = Foo(a=deque([1, 2, 3]))
    with raises(ValueError) as excinfo:
        foo.a.clear()
    assert "a: Expected length of at least 3; Got deque([])" in str(excinfo.value)


def test_clear():
    class Foo(Structure):
        a = Deque

    foo = Foo(a=deque([1, 2, 3]))
    foo.a.clear()
    assert len(foo.a) == 0


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.7 or higher")
def test_auto_mapping_of_deque():
    class Foo(Structure):
        d: deque[float]

    with raises(TypeError) as excinfo:
        Foo(d=deque([0.5, True]))
    assert "d_1: Expected <class 'float'>; Got True" in str(excinfo.value)

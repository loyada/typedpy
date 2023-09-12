import sys
from pytest import mark
from typedpy import Array, Map, Set, Structure
from typedpy.testing import find_diff


class Person(Structure):
    name: str
    age: int


class Foo(Structure):
    a: Array[str]
    i: Person

    _required = []


class Foo1(Foo):
    m: Map[str, Person]


class Bar(Structure):
    foos: Array[Foo1]
    f: Foo
    arr: list
    name: str
    s: Array[Set[Foo]]

    _required = []


foo1 = Foo1(
    m={"aaa": Person(name="john", age=12)},
    a=[],
    i=Person(name="john", age=12),
)
foo2 = Foo1(
    m={"aaa": Person(name="john", age=123)},
    a=[],
    i=Person(name="smith", age=13),
)
foo3 = Foo1(
    m={"aaa": Person(name="john", age=12), "ccc": Person(name="john", age=12)},
)
foo4 = Foo1(m={"aaa": Person(name="john", age=123), "bbb": Person(name="john", age=12)})


def test_find_diff1():
    bar1 = Bar(
        foos=[
            Foo1(
                m={"aaa": Person(name="john", age=12)},
                a=[],
                i=Person(name="john", age=12),
            ),
        ],
        arr=[1, 2, 3],
    )
    bar2 = Bar(
        foos=[
            Foo1(
                m={"aaa": Person(name="john", age=123)},
                a=[],
                i=Person(name="smith", age=13),
            )
        ],
        arr=[1, 2, 3, 6],
    )

    assert find_diff(bar2, bar1) == {
        "arr": "length of 4 vs 3",
        "foos[0]": {
            "i": {"age": "13 vs 12", "name": "smith vs john"},
            "m['aaa']": {"age": "123 vs 12"},
        },
    }

    assert find_diff(bar1, bar2) == {
        "arr": "length of 3 vs 4",
        "foos[0]": {
            "i": {"age": "12 vs 13", "name": "john vs smith"},
            "m['aaa']": {"age": "12 vs 123"},
        },
    }


def test_find_diff_order_in_list():
    bar1 = Bar(
        foos=[
            foo1,
            foo2,
            foo1,
        ],
        arr=[1, 2, 3],
    )
    bar2 = Bar(
        foos=[foo2, foo1, foo1.shallow_clone_with_overrides(a=["abc"])],
        arr=[1, 2, 3, 6],
    )

    actual = find_diff(bar1, bar2)
    assert actual == {
        "arr": "length of 3 vs 4",
        "foos": {
            "different location": ["index 0 vs 1", "index 1 vs 0", "index 2 vs 1"]
        },
        "foos[2]": {"a": "length of 1 vs 0"},
    }
    actual = find_diff(bar2, bar1)
    assert actual == {
        "arr": "length of 4 vs 3",
        "foos": {"different location": ["index 0 vs 1", "index 1 vs 0"]},
        "foos[2]": {"a": "length of 1 vs 0"},
    }


def test_find_diff_order_in_list2():
    foo5 = Foo1(
        m={"aaa": Person(name="Bob", age=123)},
        a=[],
        i=Person(name="smith", age=13),
    )

    actual = find_diff([foo1, foo2, foo2, "yyy"], [foo2, foo5, foo2, "xxx"])
    assert actual == {
        0: {
            "i": {"age": "12 vs 13", "name": "john vs smith"},
            "m['aaa']": {"age": "12 vs 123"},
        },
        1: {"m['aaa']": {"name": "Bob vs john"}},
        3: "yyy vs xxx",
        "different location": ["index 1 vs 0"],
    }
    actual = find_diff([foo2, foo5, foo2, "xxx"], [foo1, foo2, foo2, "yyy"])
    assert actual == {
        0: {
            "i": {"age": "12 vs 13", "name": "john vs smith"},
            "m['aaa']": {"age": "12 vs 123"},
        },
        1: {"m['aaa']": {"name": "Bob vs john"}},
        3: "xxx vs yyy",
        "different location": ["index 0 vs 1"],
    }


def test_find_diff_order_in_list3():
    foo3 = Foo1(
        m={"aaa": Person(name="Bob", age=123)},
        a=[],
        i=Person(name="smith", age=13),
    )

    actual = find_diff(
        [foo1, foo2, foo2, "xxx", {foo3, foo1}], [foo2, foo3, foo2, {foo3, foo2}, "xxx"]
    )
    assert actual == {
        0: {
            "i": {"age": "12 vs 13", "name": "john vs smith"},
            "m['aaa']": {"age": "12 vs 123"},
        },
        1: {"m['aaa']": {"name": "Bob vs john"}},
        3: {"class": "<class 'set'> vs. <class 'str'>"},
        4: {"class": "<class 'set'> vs. <class 'str'>"},
        "different location": ["index 1 vs 0", "index 3 vs 4"],
    }


def test_find_diff_order_in_list4():
    foo3 = Foo1(
        m={"aaa": Person(name="Bob", age=123)},
        a=[],
        i=Person(name="smith", age=13),
    )

    actual = find_diff(
        [foo1, foo2, foo2, "xxx", [foo3, foo1]],
        [foo2, foo3, foo2, "xxxx", [foo3, foo2]],
    )
    assert actual == {
        0: {
            "i": {"age": "12 vs 13", "name": "john vs smith"},
            "m['aaa']": {"age": "12 vs 123"},
        },
        1: {"m['aaa']": {"name": "Bob vs john"}},
        3: "xxx vs xxxx",
        4: {
            1: {
                "i": {"age": "12 vs 13", "name": "john vs smith"},
                "m['aaa']": {"age": "12 vs 123"},
            }
        },
        "different location": ["index 1 vs 0"],
    }


def test_find_diff_dicts():
    actual = find_diff(
        {"a": [1, 2, 3], "b": "xyz", "c": False, "e": {"ee": 2}, "g": "g"},
        {"a": [1, 3, 2], "b": 123, "c": True, "e": {"ee": 1}, "f": "xxx"},
    )
    expected = {
        "a": {"different location": ["index 1 vs 2", "index 2 vs 1"]},
        "b": {"class": "<class 'int'> vs. <class 'str'>"},
        "c": "True vs False",
        "e": {"ee": "2 vs 1"},
        "additional values": ["f"],
        "missing values": ["g"],
    }
    assert actual == expected


def test_find_diff_dict1():
    bar1 = Bar(f=foo3)
    bar2 = Bar(f=foo4, x="extra struff")

    actual = find_diff(bar1, bar2)
    assert actual == {
        "additional values": ["x"],
        "f": {
            "additional values": ["bbb"],
            "m['aaa']": {"age": "12 vs 123"},
            "missing values": ["ccc"],
        },
    }
    actual = find_diff(bar2, bar1)
    assert actual == {
        "f": {
            "m['aaa']": {"age": "123 vs 12"},
            "missing values": ["bbb"],
            "additional values": ["ccc"],
        },
        "missing values": ["x"],
    }


def test_find_diff_dict2():
    foo1 = Foo1(
        m={"aaa": Person(name="john", age=12), "ccc": Person(name="john", age=12)},
    )
    foo2 = Foo1(
        m={"aaa": Person(name="john", age=123), "bbb": Person(name="john", age=12)}
    )

    bar1 = Bar(f=foo1)
    bar2 = Bar(f=foo2, x="extra struff")

    actual = find_diff({"bar": bar1}, {"bar": bar2})
    assert actual == {
        "bar": {
            "additional values": ["x"],
            "f": {
                "additional values": ["bbb"],
                "m['aaa']": {"age": "12 vs 123"},
                "missing values": ["ccc"],
            },
        }
    }

    actual = find_diff(bar2, bar1)
    assert actual == {
        "f": {
            "additional values": ["ccc"],
            "m['aaa']": {"age": "123 vs 12"},
            "missing values": ["bbb"],
        },
        "missing values": ["x"],
    }


def test_find_diff_set():
    bar1 = Bar(s=[{foo3, foo4}, {foo4}])
    bar2 = Bar(s=[{foo4}, {foo3}])

    actual = find_diff(bar1, bar2)
    assert actual == {
        "s": {"different location": ["index 1 vs 0"]},
        "s[0]": {"missing values": [foo3]},
        "s[1]": {"additional values": [foo4], "missing values": [foo3]},
    }
    actual = find_diff(bar2, bar1)
    assert actual == {
        "s": {"different location": ["index 0 vs 1"]},
        "s[0]": {"missing values": [foo3]},
        "s[1]": {"additional values": [foo4], "missing values": [foo3]},
    }


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_find_diff_list_liststruct():
    class Foo(Structure):
        a: list[int]

    assert not find_diff(Foo(a=[1, 2, 3]), Foo.from_trusted_data({"a": [1, 2, 3]}))


def test_find_diff_list_different_length():
    diff = find_diff({"a": [1, 2]}, {"a": [1, 2, 3]})
    assert diff == {'a': 'length of 3 vs 2'}

    diff = find_diff({"a": [1, 2, 3]}, {"a": [1, 2]})
    assert diff == {'a': 'length of 2 vs 3'}

    diff = find_diff({"a": [1, 2]}, {"a": (1, 2, 3)})
    assert diff == {'a': {'class': "<class 'tuple'> vs. <class 'list'>"}}

#
# def test_assertion_err_example():
#     bar1 = Bar(
#         foos=[
#             foo1,
#             foo2,
#             foo1,
#         ],
#         arr=[1, 2, 3],
#     )
#     bar2 = Bar(
#         foos=[foo2, foo1, foo1.shallow_clone_with_overrides(a=["abc"])],
#         arr=[1, 2, 3, 6],
#     )
#
#     assert bar1 == bar2
#

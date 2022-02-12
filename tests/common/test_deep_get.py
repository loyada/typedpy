from typedpy import deep_get


def test_deep_get_with_lists():
    example = {
        "a": {
            "b": [
                {"c": [None, {"d": [1]}]},
                {"c": [None, {"d": [2]}, {"d": 3}]},
                {"c": []},
            ]
        }
    }
    assert deep_get(example, "a.b.c.d") == [[[1]], [[2], 3], []]
    assert deep_get(example, "a.b.c.d", do_flatten=True) == [1, 2, 3]
    assert deep_get(example, "a.b.c.e") == [[None], [None, None], []]
    assert deep_get(example, "a.b.c.e", do_flatten=True) == [None, None, None]


def test_deep_get_without_lists():
    example = {"a": {"b": {"c": {"d": 1}}}}
    assert deep_get(example, "a.b.c.d") == 1
    assert deep_get(example, "a.b.c.d", do_flatten=True) == 1
    assert deep_get(example, "a.b.e.d") is None
    assert deep_get(example, "a.b.e.d", do_flatten=True) is None


def test_deep_get_for_a_falsy_val():
    example = {"a": None, "b": [], "c": 0}
    assert deep_get(example, "a") is None
    assert deep_get(example, "a", default=0) is None
    assert deep_get(example, "b") == []
    assert deep_get(example, "c") == 0
    assert deep_get(example, "a.x", default=0) == 0

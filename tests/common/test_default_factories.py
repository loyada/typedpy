from typedpy.commons import default_factories


@default_factories
def f(a, b: int = 0, c=list, d=dict):
    c.append(a)
    return a, b, c, d


def test_defaults_basic_usage():
    assert f(a=1) == (1, 0, [1], {})


def test_bad_vs_good_use():
    # pylint: disable=dangerous-default-value
    def buggy_with_mutable_defaults(a, b: int = 0, c: list = [], d: dict = {}):
        c.append(a)
        return a, b, c, d

    assert buggy_with_mutable_defaults(1) == (1, 0, [1], {})
    assert buggy_with_mutable_defaults(1) == (1, 0, [1, 1], {})  # <- bug !

    assert f(1) == (1, 0, [1], {})
    assert f(1) == (1, 0, [1], {})  # correct!

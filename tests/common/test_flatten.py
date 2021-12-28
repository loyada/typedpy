from typedpy import flatten


def test_flatten():
    assert flatten([[[1]], [[2], 3, None, (5,)], []]) == [1, 2, 3, None, 5]
    assert flatten([[[1]], [[2], 3, None, (5,)], []], ignore_none=True) == [1, 2, 3, 5]

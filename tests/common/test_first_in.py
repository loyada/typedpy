from typedpy.commons import first_in


def test_first_in():
    assert first_in([1, 2]) == 1
    assert first_in([None, 1, 2, 3]) is None
    assert first_in([None, 1, 2, 3], ignore_none=True) == 1
    assert first_in([]) is None


def test_first_in_generator():
    assert first_in(range(100, 200)) is 100
    assert first_in(i for i in range(100, 200)if i>150) is 151
    assert first_in(range(0)) is None

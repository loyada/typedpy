import threading
from collections import deque

from typedpy import Deque, Deserializer, Integer, String, Structure


def _make_class():
    class Foo(Structure):
        id = String
        # heterogeneous items -- the homogeneous case (Deque[String]) shares
        # array.py's extract_field_value(), already covered by
        # test_array_thread_safety.py.
        pair = Deque(items=[String, Integer])

    return Foo


def _run_concurrently(func, num_threads=16):
    errors = []
    errors_lock = threading.Lock()
    barrier = threading.Barrier(num_threads)

    def wrapper():
        barrier.wait()
        try:
            func()
        except Exception as e:  # pylint: disable=broad-except
            with errors_lock:
                errors.append(e)

    threads = [threading.Thread(target=wrapper) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return errors


def test_deque_heterogeneous_assignment_does_not_mutate_shared_field_definition():
    # given
    Foo = _make_class()
    item0, item1 = Foo.get_all_fields_by_name()["pair"].items
    names_before = (item0._name, item1._name)

    # when
    Foo(id="f-1", pair=deque(["a", 1]))

    # then
    assert (item0._name, item1._name) == names_before


def test_deque_heterogeneous_deserialization_does_not_mutate_shared_field_definition():
    # given
    Foo = _make_class()
    item0, item1 = Foo.get_all_fields_by_name()["pair"].items
    names_before = (item0._name, item1._name)

    # when
    Deserializer(Foo).deserialize(
        {"id": "f-1", "pair": ["a", 1]}, keep_undefined=False
    )

    # then
    assert (item0._name, item1._name) == names_before


def test_concurrent_construction_of_heterogeneous_deque_field_is_safe():
    # given
    Foo = _make_class()

    # when
    errors = _run_concurrently(lambda: Foo(id="f-1", pair=deque(["a", 1])))

    # then
    assert errors == []


def test_concurrent_deserialization_of_heterogeneous_deque_field_is_safe():
    # given
    Foo = _make_class()
    payload = {"id": "f-1", "pair": ["a", 1]}

    # when
    errors = _run_concurrently(
        lambda: Deserializer(Foo).deserialize(payload, keep_undefined=False)
    )

    # then
    assert errors == []


def test_deque_heterogeneous_element_error_message_identifies_the_offending_index():
    # given
    Foo = _make_class()

    # when / then
    try:
        Foo(id="f-1", pair=deque(["a", "not an int"]))
        raise AssertionError("expected a validation error")
    except (TypeError, ValueError) as e:
        assert "pair_1" in str(e)

import threading

from typedpy import Deserializer, String, Structure, Tuple


def _make_class():
    class Foo(Structure):
        id: String
        pair: Tuple[String, String]

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


def test_tuple_assignment_does_not_mutate_shared_field_definition():
    # given
    Foo = _make_class()
    item0, item1 = Foo.get_all_fields_by_name()["pair"].items
    names_before = (item0._name, item1._name)

    # when
    Foo(id="f-1", pair=("a", "b"))

    # then
    assert (item0._name, item1._name) == names_before


def test_tuple_deserialization_does_not_mutate_shared_field_definition():
    # given
    Foo = _make_class()
    item0, item1 = Foo.get_all_fields_by_name()["pair"].items
    names_before = (item0._name, item1._name)

    # when
    Deserializer(Foo).deserialize(
        {"id": "f-1", "pair": ["a", "b"]}, keep_undefined=False
    )

    # then
    assert (item0._name, item1._name) == names_before


def test_concurrent_construction_of_tuple_field_is_safe():
    # given
    Foo = _make_class()

    # when
    errors = _run_concurrently(lambda: Foo(id="f-1", pair=("a", "b")))

    # then
    assert errors == []


def test_concurrent_deserialization_of_tuple_field_is_safe():
    # given
    Foo = _make_class()
    payload = {"id": "f-1", "pair": ["a", "b"]}

    # when
    errors = _run_concurrently(
        lambda: Deserializer(Foo).deserialize(payload, keep_undefined=False)
    )

    # then
    assert errors == []


def test_tuple_element_error_message_identifies_the_offending_index():
    # given
    Foo = _make_class()

    # when / then
    try:
        Foo(id="f-1", pair=("a", 5))
        raise AssertionError("expected a validation error")
    except (TypeError, ValueError) as e:
        assert "pair_1" in str(e)

import threading

from typedpy import Deserializer, Set, String, Structure


def _make_merchant_class():
    # a fresh class per test, so no test's mutation of shared field state
    # leaks into another test via a module-level class object.
    class Merchant(Structure):
        id: String
        tags: Set[String]

    return Merchant


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


def test_set_assignment_does_not_mutate_shared_field_definition():
    # given
    Merchant = _make_merchant_class()
    items = Merchant.get_all_fields_by_name()["tags"].items
    name_before = items._name

    # when
    Merchant(id="m-1", tags={"a", "b", "c"})

    # then
    assert items._name == name_before


def test_set_deserialization_does_not_mutate_shared_field_definition():
    # given
    Merchant = _make_merchant_class()
    items = Merchant.get_all_fields_by_name()["tags"].items
    name_before = items._name

    # when
    Deserializer(Merchant).deserialize(
        {"id": "m-1", "tags": ["a", "b"]}, keep_undefined=False
    )

    # then
    assert items._name == name_before


def test_concurrent_construction_of_set_field_is_safe():
    # given
    Merchant = _make_merchant_class()
    tags = {"a", "b", "c", "d", "e", "f", "g", "h"}

    # when
    errors = _run_concurrently(lambda: Merchant(id="m-1", tags=tags))

    # then
    assert errors == []


def test_concurrent_deserialization_of_set_field_is_safe():
    # given
    Merchant = _make_merchant_class()
    payload = {"id": "m-1", "tags": ["a", "b", "c", "d", "e", "f", "g", "h"]}

    # when
    errors = _run_concurrently(
        lambda: Deserializer(Merchant).deserialize(payload, keep_undefined=False)
    )

    # then
    assert errors == []

import threading

from typedpy import Array, Deserializer, String, Structure


class Industry(Structure):
    id: String
    name: String


class Merchant(Structure):
    id: String
    industry: Array[Industry]


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


def test_array_assignment_does_not_mutate_shared_field_definition():
    # given
    items = Merchant.get_all_fields_by_name()["industry"].items
    name_before = items._name

    # when
    Merchant(id="m-1", industry=[Industry(id=str(i), name=str(i)) for i in range(4)])

    # then
    assert items._name == name_before


def test_array_deserialization_does_not_mutate_shared_field_definition():
    # given
    items = Merchant.get_all_fields_by_name()["industry"].items
    name_before = items._name

    # when
    Deserializer(Merchant).deserialize(
        {"id": "m-1", "industry": [{"id": "1", "name": "one"}]}, keep_undefined=False
    )

    # then
    assert items._name == name_before


def test_concurrent_construction_of_array_field_is_safe():
    # given
    industries = [Industry(id=str(i), name=str(i)) for i in range(8)]

    # when
    errors = _run_concurrently(lambda: Merchant(id="m-1", industry=industries))

    # then
    assert errors == []


def test_concurrent_deserialization_of_array_field_is_safe():
    # given
    payload = {
        "id": "m-1",
        "industry": [{"id": str(i), "name": str(i)} for i in range(8)],
    }

    # when
    errors = _run_concurrently(
        lambda: Deserializer(Merchant).deserialize(payload, keep_undefined=False)
    )

    # then
    assert errors == []


def test_element_error_message_identifies_the_offending_index():
    # given
    class Foo(Structure):
        a: Array[String]

    # when / then
    for bad_input, expected in [
        ({"a": ["ok", 5]}, "a_1"),
        ({"a": [5]}, "a_0"),
    ]:
        try:
            Deserializer(Foo).deserialize(bad_input, keep_undefined=False)
            raise AssertionError("expected a validation error")
        except (TypeError, ValueError) as e:
            assert expected in str(e)

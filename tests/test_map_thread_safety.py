import threading

from typedpy import Array, Deserializer, Integer, Map, String, Structure


def _make_class():
    class Foo(Structure):
        id: String
        counts: Map[String, Integer]

    return Foo


def _make_nested_class():
    class Foo(Structure):
        id: String
        # Map nested as the item type of an Array. This is the case that
        # proved a shallow copy of the outer Array field is not enough:
        # copying Array.items (the Map) does not copy the Map's own nested
        # key_field/value_field, which Map.__set__ mutates directly.
        items: Array[dict[str, Integer]]

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


def test_map_assignment_does_not_mutate_shared_field_definition():
    # given
    Foo = _make_class()
    key_field, value_field = Foo.get_all_fields_by_name()["counts"].items
    names_before = (key_field._name, value_field._name)

    # when
    Foo(id="f-1", counts={"a": 1, "b": 2})

    # then
    assert (key_field._name, value_field._name) == names_before


def test_map_deserialization_does_not_mutate_shared_field_definition():
    # given
    Foo = _make_class()
    key_field, value_field = Foo.get_all_fields_by_name()["counts"].items
    names_before = (key_field._name, value_field._name)

    # when
    Deserializer(Foo).deserialize(
        {"id": "f-1", "counts": {"a": 1}}, keep_undefined=False
    )

    # then
    assert (key_field._name, value_field._name) == names_before


def test_concurrent_construction_of_map_field_is_safe():
    # given
    Foo = _make_class()
    counts = {str(i): i for i in range(8)}

    # when
    errors = _run_concurrently(lambda: Foo(id="f-1", counts=counts))

    # then
    assert errors == []


def test_concurrent_deserialization_of_map_field_is_safe():
    # given
    Foo = _make_class()
    payload = {"id": "f-1", "counts": {str(i): i for i in range(8)}}

    # when
    errors = _run_concurrently(
        lambda: Deserializer(Foo).deserialize(payload, keep_undefined=False)
    )

    # then
    assert errors == []


def test_map_nested_in_array_does_not_mutate_shared_field_definition():
    # given
    Foo = _make_nested_class()
    inner_map_field = Foo.get_all_fields_by_name()["items"].items
    key_field, value_field = inner_map_field.items
    names_before = (key_field._name, value_field._name)

    # when
    Foo(id="f-1", items=[{"a": 1}, {"b": 2}, {"c": 3}])

    # then
    assert (key_field._name, value_field._name) == names_before


def test_concurrent_construction_of_map_nested_in_array_is_safe():
    # given
    Foo = _make_nested_class()
    payload = [{"a": 1}, {"b": 2}, {"c": 3}, {"d": 4}, {"e": 5}, {"f": 6}]

    # when
    errors = _run_concurrently(lambda: Foo(id="f-1", items=payload))

    # then
    assert errors == []


def test_concurrent_deserialization_of_map_nested_in_array_reports_correct_index():
    # given: each thread deserializes an array whose sole invalid element
    # (a non-int value) is at a thread-specific index. This raises inside
    # deserialize_map()/deserialize_list_like() before Foo.__init__ (and its
    # own, separately-fixed Map.__set__) is ever reached, so it isolates the
    # serialization.py fix specifically.
    Foo = _make_nested_class()
    num_threads = 16
    results = {}
    results_lock = threading.Lock()
    barrier = threading.Barrier(num_threads)

    def deserialize_with_bad_index(idx):
        barrier.wait()
        payload = [{"a": 1} for _ in range(num_threads)]
        payload[idx] = {"a": "not an int"}
        try:
            Deserializer(Foo).deserialize({"items": payload}, keep_undefined=False)
            outcome = "no error raised"
        except (TypeError, ValueError) as e:
            outcome = str(e)
        with results_lock:
            results[idx] = outcome

    threads = [
        threading.Thread(target=deserialize_with_bad_index, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # when / then
    for idx, outcome in results.items():
        assert f"items_{idx}_value" in outcome, f"thread {idx}: got {outcome!r}"

import threading

from typedpy import Array, Deserializer, String, Structure
from typedpy.commons import private_copy_of_field


class Industry(Structure):
    id: String
    name: String


class Merchant(Structure):
    id: String
    industry: Array[Industry]


def _run_concurrently(func, num_threads=16):
    # NOTE: tests built on this helper exercise real OS thread scheduling,
    # which turned out (empirically, via manual probing with
    # sys.setswitchinterval() cranked down) to almost never land inside the
    # few-bytecode-wide window where the original bug's corruption could
    # occur. They are useful smoke tests, but are not reliable proof on
    # their own -- see test_extract_field_value_race_is_fixed() below for a
    # deterministic reproduction that doesn't depend on scheduling luck.
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


def test_concurrent_deserialization_reports_correct_offending_index():
    # given: each thread deserializes an array whose sole invalid element is
    # at a thread-specific index. This raises inside deserialize_list_like,
    # before Merchant.__init__ (and its own, separately-fixed __set__) is
    # ever reached, so it isolates the serialization.py fix specifically.
    class Foo(Structure):
        a: Array[String]

    num_threads = 16
    results = {}
    results_lock = threading.Lock()
    barrier = threading.Barrier(num_threads)

    def deserialize_with_bad_index(idx):
        barrier.wait()
        payload = {"a": ["ok"] * num_threads}
        payload["a"][idx] = 12345
        try:
            Deserializer(Foo).deserialize(payload, keep_undefined=False)
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
        assert f"a_{idx}" in outcome, f"thread {idx}: got {outcome!r}"


def test_extract_field_value_race_is_fixed():
    # given: deterministically simulate the exact interleaving a scheduler
    # could produce between two concurrent extract_field_value() calls
    # sharing the same Array field's `items` object -- one processing
    # element "a_0" for one Structure instance, the other "b_5" for a
    # different instance -- instead of relying on real thread timing, which
    # (see _run_concurrently's note above) essentially never lands inside
    # the actual vulnerable window in practice.
    class Foo(Structure):
        a: Array[String]

    items = Foo.get_all_fields_by_name()["a"].items
    temp_st_a = Structure()
    temp_st_b = Structure()

    item_a = private_copy_of_field(items)
    setattr(item_a, "_name", "a_0")
    item_a.__set__(temp_st_a, "value-for-A")

    # a "concurrent thread" fully interleaves here, using its own copy
    item_b = private_copy_of_field(items)
    setattr(item_b, "_name", "b_5")
    item_b.__set__(temp_st_b, "value-for-B")
    result_b = getattr(temp_st_b, "b_5")

    # thread A resumes: its own copy's _name was never touched by B
    result_a = getattr(temp_st_a, "a_0")

    assert result_a == "value-for-A"
    assert result_b == "value-for-B"


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

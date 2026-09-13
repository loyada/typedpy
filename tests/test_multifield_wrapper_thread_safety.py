import threading

from typedpy import (
    AllOf,
    AnyOf,
    Array,
    Deserializer,
    Integer,
    NotField,
    OneOf,
    Positive,
    String,
    Structure,
)


def _make_anyof_class():
    class Foo(Structure):
        id: String
        value: AnyOf[Integer, String]

    return Foo


def _make_anyof_nested_class():
    class Foo(Structure):
        id: String
        # AnyOf nested as the item type of an Array -- same shallow-copy gap
        # as Map nested in Array: copying Array.items (the AnyOf) does not
        # copy the AnyOf's own candidate fields, which AnyOf.__set__ mutates
        # directly.
        values: Array[AnyOf[Integer, String]]

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


def test_anyof_assignment_does_not_mutate_shared_field_definitions():
    # given
    Foo = _make_anyof_class()
    int_field, str_field = Foo.get_all_fields_by_name()["value"].get_fields()
    names_before = (int_field._name, str_field._name)

    # when
    Foo(id="f-1", value=5)

    # then
    assert (int_field._name, str_field._name) == names_before


def test_concurrent_construction_of_anyof_field_is_safe():
    # given
    Foo = _make_anyof_class()

    # when
    errors = _run_concurrently(lambda: Foo(id="f-1", value=5))

    # then
    assert errors == []


def test_anyof_nested_in_array_does_not_mutate_shared_field_definitions():
    # given
    Foo = _make_anyof_nested_class()
    inner_anyof = Foo.get_all_fields_by_name()["values"].items
    int_field, str_field = inner_anyof.get_fields()
    names_before = (int_field._name, str_field._name)

    # when
    Foo(id="f-1", values=[1, "a", 2, "b"])

    # then
    assert (int_field._name, str_field._name) == names_before


def test_concurrent_construction_of_anyof_nested_in_array_is_safe():
    # given
    Foo = _make_anyof_nested_class()
    values = [1, "a", 2, "b", 3, "c", 4, "d"]

    # when
    errors = _run_concurrently(lambda: Foo(id="f-1", values=values))

    # then
    assert errors == []


def test_concurrent_deserialization_of_anyof_nested_in_array_reports_correct_index():
    # given: each thread deserializes an array whose sole invalid element
    # (matching neither Integer nor String) is at a thread-specific index.
    # This raises inside deserialize_multifield_wrapper()/
    # deserialize_list_like() before Foo.__init__ (and its own, separately-
    # fixed AnyOf.__set__) is ever reached, so it isolates the
    # serialization.py fix specifically.
    Foo = _make_anyof_nested_class()
    num_threads = 16
    results = {}
    results_lock = threading.Lock()
    barrier = threading.Barrier(num_threads)

    def deserialize_with_bad_index(idx):
        barrier.wait()
        payload = [1] * num_threads
        payload[idx] = 3.14
        try:
            Deserializer(Foo).deserialize({"values": payload}, keep_undefined=False)
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
        assert f"values_{idx}: Expected <class 'int'>" in outcome, (
            f"thread {idx}: got {outcome!r}"
        )


def test_oneof_assignment_does_not_mutate_shared_field_definitions():
    # given
    class Foo(Structure):
        id: String
        value: OneOf[Integer, String]

    int_field, str_field = Foo.get_all_fields_by_name()["value"].get_fields()
    names_before = (int_field._name, str_field._name)

    # when
    Foo(id="f-1", value=5)

    # then
    assert (int_field._name, str_field._name) == names_before


def test_allof_assignment_does_not_mutate_shared_field_definitions():
    # given
    class Foo(Structure):
        id: String
        value: AllOf[Integer, Positive]

    int_field, positive_field = Foo.get_all_fields_by_name()["value"].get_fields()
    names_before = (int_field._name, positive_field._name)

    # when
    Foo(id="f-1", value=5)

    # then
    assert (int_field._name, positive_field._name) == names_before


def test_notfield_assignment_does_not_mutate_shared_field_definitions():
    # given
    class Foo(Structure):
        id: String
        value: NotField[Integer]

    (int_field,) = Foo.get_all_fields_by_name()["value"].get_fields()
    name_before = int_field._name

    # when
    Foo(id="f-1", value="not an int")

    # then
    assert int_field._name == name_before

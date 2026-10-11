================
Common Utilities
================


.. currentmodule:: typedpy

.. contents:: :local:


.. autofunction:: deep_get

.. autofunction:: nested

.. autofunction:: flatten

.. autofunction:: default_factories


Testing Utilities
=================

.. currentmodule:: typedpy.testing

.. autofunction:: find_diff


Showing the Differences in Failed pytest Assertions
---------------------------------------------------
Typedpy includes a pytest hook that uses :func:`find_diff` to explain a failed assertion that two Structures are
equal. To enable it, import it in your ``conftest.py``:

.. code-block:: python

    # conftest.py
    from typedpy.testing import pytest_assertrepr_compare  # noqa: F401

Then, a failing ``assert actual == expected`` between two Structures shows exactly what is different, including in
nested Structures and collections:

.. code-block:: python

    class Address(Structure):
        city: str
        zip_code: str

    class Person(Structure):
        name: str
        age: int
        address: Address
        tags: list[str]
        scores: Map[str, int]

    def test_people_equal():
        expected = Person(name="Joe", age=30, address=Address(city="NY", zip_code="10001"),
                          tags=["a", "b"], scores={"math": 90, "art": 80})
        actual = Person(name="Joe", age=31, address=Address(city="NY", zip_code="10002"),
                        tags=["b", "a"], scores={"math": 90, "music": 70})
        assert actual == expected

The failure message is:

.. code-block:: text

    found the following differences between the structures:
    {"address": {"zip_code": "10002 vs 10001"}, "age": "31 vs 30", "scores": {"missing values": ["music"], "additional values": ["art"]}, "tags": {"different location": ["index 0 vs 1", "index 1 vs 0"]}}

Values that appear on the left side of the comparison but not on the right side are listed under "missing values",
and values that appear on the right side but not on the left side are listed under "additional values". In the
example above, "music" appears in ``actual`` but not in ``expected``, so it is listed under "missing values".

To print the differences as indented JSON, one entry per line, set:

.. code-block:: python

    # conftest.py
    from typedpy.structures import TypedPyDefaults

    TypedPyDefaults.pretty_print_pytest_diff = True

Then the failure message above becomes:

.. code-block:: text

    found the following differences between the structures:
    {
      "address": {
        "zip_code": "10002 vs 10001"
      },
      "age": "31 vs 30",
      "scores": {
        "missing values": [
          "music"
        ],
        "additional values": [
          "art"
        ]
      },
      "tags": {
        "different location": [
          "index 0 vs 1",
          "index 1 vs 0"
        ]
      }
    }

Note that pytest truncates long assertion messages to about 8 lines, unless running with ``-vv``, so the indented
format is most useful together with ``-vv``.

Verifying Trusted Deserialization Compatibility
-----------------------------------------------
See :ref:`trusted-deserialization`.

.. autofunction:: assert_trusted_deserialization_mapper_is_safe

======================
Support for Versioning
======================


.. currentmodule:: typedpy

.. contents:: :local:


The use-case for support for versioning Typedpy addresses is deserializing different versions of the dictionary representing \
the structure to match the latest Structure definition.

For example, suppose you saved a JSON object that adheres to some strict schema, and occasionally that schema had to evolve \
to include new fields, or update existing ones. When you read it again, you always want to map to the latest schema, which \
is what you are currently using.


The requirement: Typedpy expects the dictionary to have a "version" field, that has increasing consecutive integer values, \
starting from 1.
Next, you need to provide a list of mappers. Each mapper defines how to convert from the corresponding version to the next.
These mappers are, in general, similar to the regular "serialization mappers" of Typedpy, but they add 2 new features:

1. Constant(val) - the value is a constant. This is useful when you introduced a new field in a more recent version and
   you want to define that when converting older versions, we need to populate it with a default value.

2. Deleted - The newer version no longer has this field, and it should be dropped


Typedpy has two types of API's to handle it.

Low-Level API
-------------

Example of usage:

.. code-block:: python

    versions_mapping = [
            # Mapping from version 1 to 2
        {
            "j": Constant(100),
            "old_bar._mapper": {
                "a": FunctionCall(func=lambda x: [i * 2 for i in x], args=["a"]),
            },
            "old_m": Constant({"abc": "xyz"})
        },

            # mapping from version 2 to 3
        {
            "old_bar._mapper": {
                "s": "sss",
                "sss": Deleted
            },
            "bar": "old_bar",
            "m": "old_m",
            "old_m": Deleted,
            "old_bar": Deleted,
        },

            # mapping from version 3 to 4
        {
            "i": FunctionCall(func=lambda x: x * 100, args=["i"])
        }
    ]

    in_version_1 = {
        "version": 1,
        "old_bar": {
            "a": [5, 8, 2],
            "sss": "john",
        },
        "i": 2,
        "old_m": {"a": "aa", "b": "bb"}
    }

    assert convert_dict(in_version_1, versions_mapping) == {
        "version": 4,
        "bar": {
            "a": [10, 16, 4],
            "s": "john",
        },
        "i": 200,
        "j": 100,
        "m": {"abc": "xyz"},
    }

*Explanation*: The function convert_dict will apply all the applicable mappings based on the version of the input. In
this case, it needs to replay all the mapping, since the raw input is at version 1.

To further illustrate, let's follow the steps.

After the first mapper (i.e. version 2), the input looks like:

.. code-block:: python

    {'version': 2, 'old_bar': {'a': [10, 16, 4], 'sss': 'john'}, 'i': 2, 'old_m': {'abc': 'xyz'}, 'j': 100}


After the the second mapper (i.e. version 3), the input looks like:

.. code-block:: python

    {'version': 3, 'i': 2, 'j': 100, 'bar': {'a': [10, 16, 4], 's': 'john'}, 'm': {'abc': 'xyz'}}


And finally, after the last mapper, it looks like:

.. code-block:: python

    {'version': 4, 'i': 200, 'j': 100, 'bar': {'a': [10, 16, 4], 's': 'john'}, 'm': {'abc': 'xyz'}}



High-Level API
--------------

Typedpy defines a special Structure that is effectively a marker for a versioned structure: :class:`Versioned`

.. autoclass:: Versioned


The example below clarifies how to use :class:`Versioned` together with deserializer.

.. code-block:: python


    class Foo(Versioned, ImmutableStructure):
        bar: Bar
        i: Integer
        j: Integer
        m: Map[String, String]

        _versions_mapping = [
            {   # version 1 -> 2
                "j": Constant(100),
                "old_bar._mapper": {
                    "a": FunctionCall(func=lambda x: [i * 2 for i in x], args=["a"]),
                },
                "old_m": Constant({"abc": "xyz"})
            },

            {   # version 2 -> 3
                "old_bar._mapper": {
                    "s": "sss",
                    "sss": Deleted
                },
                "bar": "old_bar",
                "m": "old_m",
                "old_m": Deleted,
                "old_bar": Deleted,
            },

            {   # version 3 -> 4
                "i": FunctionCall(func=lambda x: x * 100, args=["i"])
            }

        ]


    # Once defined, the deserializer applies the versions conversion as the first step.
    # For example:
    in_version_1 = {
        "version": 1,
        "old_bar": {
            "a": [5, 8, 2],
            "sss": "john",
        },
        "i": 2,
        "old_m": {"a": "aa", "b": "bb"}
    }
    assert Deserializer(Foo).deserialize(in_version_1) == Foo(
        bar=Bar(a=[10, 16, 4], s="john"),
        m={"abc": "xyz"},
        i=200,
        j=100,
        version=4
    )


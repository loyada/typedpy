=================
Structures
=================


.. currentmodule:: typedpy

.. contents:: :local:

The Basics - Usage
==================

Typedpy allows to define strict structures easily, by extending from :class:`Structure`.
A simple example:

.. code-block:: python

    from typedpy import Structure, Integer, Array, Map, Number, String, PositiveFloat

    class Example(Structure):
        name = String
        val_by_alias = Map[String, Number]
        num = Integer(maximum=30)
        foo = Array[PositiveFloat]


This structure validates itself, so that any attempt to create an invalid structure will raise an exception.


.. autoclass:: Structure


Immutability
============
.. autoclass:: ImmutableStructure


Structure As Field
==================
See :ref:`structure-as-field`

Inlined Structure
=================
See :ref:`structure-inlining`

Structure Inheritance
=====================
Structure inheritance is fully supported and works the way you would expect.
Required properties are the union of all required properties.

`Here is a test for inheritance <https://github.com/loyada/typedpy/tree/master/tests/test_inheritance.py>`_


Combining with "Regular" Classes
================================

Combining a structure with regular classes is straightforward.
The only thing to remember, is that if you override the constructore, it must call the super() constructor.
Example:

.. code-block:: python

    class Example(Structure):
        num = Integer(minimum=10)
        st = String

    class Foo(Example):
        def __init__(self, *args, x, y, **kwargs):
            self.x = x
            self.y = y
            super().__init__(*args, **kwargs)

        def multiply_xy_num(self):
            return self.x * self.y * self.num


    foo = Foo(st = "abc", num = 10, x = 2, y = 3)
    print(foo.multiply())
    # 60

Validating Structure As a Whole
===============================
There are cases where we want to validate a complex field, or a structure as a whole.
For example, suppose we define a range field and we want to ensure min is not larger than max.
There are 2 ways to approach it.
First approach: create a regular class and provide a validation function, as described in :ref:`extension-of-classes`
For example:

.. code-block:: python

    class RangeCL(object):
        def __init__(self, min, max, step):
            self.min = min
            self.max = max
            self.step = step


    def validate_range(range):
        if not isinstance(range.min, (float, int, Decimal)):
            raise TypeError()
        if range.min > range.max:
            raise ValueError()

    ValidatedRangeField = create_typed_field("RangeField", RangeCL, validate_func=validate_range)

    # now we can use ValidatedRangeField as a field type. It is guaranteed to be valid.
    class Foo(Structure):
        range = ValidatedRangeField

The second approach is to override  the __validate__ function of the structure.
For example:

.. code-block:: python

    class Range(Structure):
        min = Integer
        max = Integer
        step = Integer
        _required = ["min", "max"]

        def __validate__(self):
            if self.min > self.max:
                raise ValueError("min cannot be larger than max")


In the example above, any Range instance is guaranteed to be valid, even if you mutate it.

| Of the two approaches described, usually the second approach is more elegant.

`See usage of both approaches here <https://github.com/loyada/typedpy/tree/master/tests/test_higher_order.py>`_

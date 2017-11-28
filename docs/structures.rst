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
        str = String

    class Foo(Example):
        def __init__(self, *args, x, y, **kwargs):
            self.x = x
            self.y = y
            super().__init__(*args, **kwargs)

        def multiply_xy_num(self):
            return self.x * self.y * self.num


    foo = Foo(str = "abc", num = 10, x = 2, y = 3)
    print(foo.multiply())
    # 60


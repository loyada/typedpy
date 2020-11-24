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
        name: String
        counts_by_alias: Map[String(pattern='[A-Za-z]+$'), Positive]
        num: Integer(maximum=30) = 1
        foo: Array[PositiveFloat]

This structure validates itself, so that any attempt to create an invalid structure will raise an exception.

**Recent updates - Version 2.0**
While still supporting the old-style :class:`Structure` definition, which looks as follows:

.. code-block:: python

    class Example(Structure):
        name = String
        counts_by_alias = Map[String(pattern='[A-Za-z]+$'), Positive]
        num = Integer(maximum=30, default=1)
        foo = Array[PositiveFloat]


* All fields are public, and fields names are not allowed to start with "_", since it implies non-public attributes.




After version 2.0, you can also use dataclass-style definition. Look at the following examples:

.. code-block:: python

   class Example_New_Style(Structure):
        name: String
        counts_by_alias: Map[String(pattern='[A-Za-z]+$'), Positive]
        num: Integer(maximum=30) = 1
        foo: Array[PositiveFloat]


    # all the types here will be automatically converted to their corresponding
    # Typedpy equivalent This includes support for PEP 585 (even on Python 3.6!)
    class Example_New_Style_Mixed_With_Typing_Types(Structure):
        name: str
        counts_by_alias: Dict[str, Positive]
        id: Union[Integer(minimum=1000), String(pattern='[0-9]+$')] = 1
        foo: Array[PositiveFloat]


    class Example_With_AutoWrapping_Of_Any_Class(Structure):
        # assume Point and Person below are arbitrary, non-Typedpy, user classes
        points: list[Point]
        person: Field[Person]

| If you look carefully, you might be confused as there are multiple ways to define similar things, for example an
| array field can be defined as Array, typing.List, list, Field[list]. What is the right one to use?
| If you use a recent version of Typepy, all of these are supported.
| However, here are some guidelines:


#. Before version 1.35 you have to use Array
#. Version 2.0 allows to use list, typing.List. They are converted automatically to a Typedpy :class:`Array`, thus enjoying other features of Typepy automatically.
#. After version 2.0 Typepy also supports implicit conversion of any class to a Typedpy field, thus you can use Field[list]. The disadvantage of this style is that Typedpy knows nothing about the field except its type, so serialization is done only on a best effort basis, pickling and JSON schema mapping is unsupported for any Structure with implicit mapping. Typedpy offers API to explicitly create Typedpy Field types that correspond to non-Typedpy classes, and if you don't mind the extra code, it is more flexible.
#. Wherever you can, prefer to use the Typedpy classes. They provide the richest API support and are the most rigorously tested.



.. autoclass:: Structure


Required Fields and Optional Fields
===================================
| By using the **_required** property in the class definition, we can define a list of fields that are required.
| This means that if not all of them are provided in the instantiation, then Typedpy will raise and appropriate exception.
| By default, all the fields are required.
| In case it is simpler to describe the fields that are optional (for example, we have 10 fields and only one
  of them is optiona), we can use the **_optional** property.
| If **_required** property is stated, the **_optional** will be ignored.
|
| Every field that has a default value is, by definition, optional.
|
| A recent (version > 2.0.1) addition is the support of **typing.Optional** field. using Optional[MyFieldType] is
| equivalent to defining it as one of fields in the **_optional** list.
| Alternatively, you could use: AnyOf[MyFieldType, NoneField], which is the internal implementation of **Optional**
| in Typedpy.

To demonstrate, the three classes below are equivalent, as far as fields optionality:

.. code-block:: python

    class Example1(Structure):
        name: String
        val_by_alias: Map[String, Number]
        my_list: Array[PositiveFloat]
        _required = ['name', 'val_by_alias']

    class Example2(Structure):
        name: String
        val_by_alias: Map[String, Number]
        my_list: Array[PositiveFloat]
        _optional = ['my_list']

    from typing import Optional

    class Example3(Structure):
        name: String
        val_by_alias: Map[String, Number]
        my_list: Optional[Array[PositiveFloat]]

The only difference between the first two and the third is that in the third you can actually
assign **None** to my_list (i.e. instance.my_list = None), while in the others it is not allowed.


Defaults
========
| Every field can come with a default value, which implicitly makes it an optional field.
| Default values are validated like any other value in the definition of the field or class , which helps prevent
| developer's mistakes early. An invalid default will raise exception. For example, the following code raises
| a TypeError, with a clear error message:

.. code-block:: python

    class Example(Structure):
        i: Array[Integer] = [1, 2, "x"]
        s: String(default="xyz")

| As can be seen above, there are two ways to define default values: as a parameter to field constructor or
| with an equality.


Immutability
============
| Typepy supports immutable structures. Such structures are protected from any update after instantiation. In most
| cases trying to do so will raise an appropriate exception. There are cases that Typepy can't know that the developer
| is trying to change the structure, but even then, Typepy blocks such attempts by using defensive copies.
| Be aware immutable structures tend to be somewhat slower.

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

Equality Checks
===============
Equality check (i.e. checking a==b) of structures is fully supported, including for arbitrarily complex objects.

String output
=============
The string representation of structure instances shows exactly what are all the properties, even for hierarchical \
structures and arbitrarily complex ones. This is useful for debugging.

Other Magic Methods Support
===========================
Typepy supports the following operations for structure instances:

* If your Structure is a wrapper for a collection, you can ask if an item is in it:

.. code-block:: python

    class Foo(Structure):
        s = Map[String, Anything]
        _additionalProperties = False

    f = Foo(s={'xxx': 123, 'yyy': 234, 'zzz': 'zzz'})
    assert 'xxx' in f
    assert 123 not in f


* Hash functions

* Copy, deepcopy

* dir(structure_instance) returns all the field names in the instance

* pickle (with the exception of StructuredReference)

* "As boolean" operator. For example:

.. code-block:: python

    assert not Example()
    assert Example(i=5)

Combining with "Regular" Classes
================================

Combining a structure with regular classes is straightforward.
The only thing to remember, is that if you override the constructor, it must call the super() constructor.
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

Validating a Structure As a Whole
=================================
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

Alternative Syntax
==================
(starting at version 1.35)
Since many are used to the Dataclasses syntax, Typedpy supports its format for defining fields in the structure class. \
Furthermore, if provided with standard builtin types, it will convert them automatically to their equivalent Typedpy \
Field types.

So, the following class

.. code-block:: python

    class Foo(Structure):
        i: Integer = 10
        s: String(maxLength=10)
        map = Map[String, Integer]
        bar: Bar
        s1: str
        m: list = [1,2,3]

Is converted by Typedpy automatically to this:

.. code-block:: python

    class Foo(Structure):
        i = Integer(default=10)
        s = String(maxLength=10)
        map = Map[String, Integer]
        bar = Bar
        s1 = String
        m = Array(default=[1,2,3])

This provides you with all the run-time checking and other typedpy functionality even if you use regular Python types.
It also applies default values (see fields 'm', 'i' above).

Two examples:

.. code-block:: python

    class Example1(Structure):
        i: int
        f: float
        mylist: list
        map: dict

    e = Example1(i=1, f=0.5, mylist=['x'], map={'x': 'y'})

    # the following line will throw a TypeError with the message: "mylist: Got 7; Expected <class 'list'>"
    e.mylist = 7


    class ExampleOfImmutable(ImmutableStructure):
        i: Integer = 5
        mylist: list = [1,2]
        map: dict

    e = ExampleOfImmutable(i=1, map={'x': 'y'})

    assert e.mylist == [1,2]

    # the following line will throw a ValueError with the message: "Structure is immutable"
    e.mylist.append(3)


=================
Fields
=================


.. currentmodule:: typedpy

.. contents:: :local:

The Basics - Usage
==================

Each field is a class. Using it has two variations: the simplified form is just the class names. For example:

.. code-block:: python

    names = Array[String]
    name_and_age = Tuple[String, PositiveFloat]
    age_by_name = Map[Sring, PositiveFloat]
    name = String
    quantity = Number

However, if more restriction are required, they need to be passed to the constructor. For Example:

.. code-block:: python

    name = Number(String(pattern='[A-Za-z]+$', maxLength=20)

Predefined Types
================

.. autoclass:: Field

.. autoclass:: Anything

Numerical
---------

:mod:`typedpy` defines the following basic field types:

.. autoclass:: Number

.. autoclass:: Integer

.. autoclass:: Float

.. autoclass:: Positive

.. autoclass:: PositiveFloat

.. autoclass:: PositiveInt

.. autoclass:: Boolean

String, Enums etc.
------------------

.. autoclass:: String

.. autoclass:: Enum

.. autoclass:: EnumString

.. autoclass:: Sized

.. autoclass:: DateString

.. autoclass:: TimeString

.. autoclass:: IPV4

.. autoclass:: JSONString

.. autoclass:: HostName

.. autoclass:: DecimalNumber

.. class:: EmailAddress

            String of an email address



Collections
-----------

.. autoclass:: Array

.. autoclass:: Set

.. autoclass:: Tuple

.. autoclass:: Map


* **Note** - The collections support embedded collections, such as :class:`Array` [ :class:`Tuple` [ :class:`Integer` , :class:`Integer` ]]

**All collections support reference to another** :class:`Structure` . For example, this code is valid and will work the
way you'd expect:

.. code-block:: python

    class Foo(Structure):
          s = String

    class Bar(Structure):
          a = Set[Foo]
          b = Map [Foo, Integer]



Re-use
======

.. autoclass:: AllOf

.. autoclass:: AnyOf

.. autoclass:: OneOf

.. autoclass:: NotField

**All the field types under this category support reference to another** :class:`Structure` . For example, this code is valid and will work the
way you'd expect:

.. code-block:: python

    class Foo(Structure):
          s = String

    class Bar(Structure):
          a = Any[Foo, Integer]

Inheritance and mixins
----------------------
Inheritance works the way you would expect:

.. code-block:: python

    # define a new mixin
    class Even(Field):
        def __set__(self, instance, value):
            if value % 2 > 0:
                raise ValueError('Must be even')
            super().__set__(instance, value)

    class EvenPositiveInt(Integer, Positive, Even): Pass

    # Done! Now we have a new Field type that we can use



.. _structure-as-field:

Using a Structure as a Field
----------------------------
Any Structure type can also be used as a field.

.. code-block:: python

    # Suppose we defined a new structure "Foo":
    class Foo(Structure):
        st = String

    # We can now use it as a Field:
    class Example(Structure):
        a = Foo
        b = Array[Foo]
        c = AnyOf[Foo, Integer]

    #This will raise a TypeError for a
    Example(a = 1, b=[], c=2)

    #This is valid
    Example(a=Foo(st=""), b=[Foo(st="xyz")], c=2))

.. _structure-inlining:

Inlining a Structure as a Field
-------------------------------
.. autoclass:: StructureReference


Immutability
============
To define an immutable Field, you use the mixin **ImmutableField**.
Example:

.. code-block:: python

    class ImmutableString(String, ImmutableField): pass

    class A(Structure):
        x = Number
        y = ImmutableString


    a = A(x=0.5, y="abc")

    # This will raise an ValueError exception, with the message  "y: Field is immutable"
    a.y += "xyz"


It is also possible to define an immutable Structure. See Under the **Structures** section.

Optional Field and Default Values
=================================
A structure can have fields that are optional. For an optional field, if no value is provided, then the assessor returns
None by default.
You can provide a default settings, using the "default"  parameter (see below). If a default value is set and no value is provided, then the assessor returns the default value.
Example:

.. code-block:: python

    class Person(Structure):
        _required = ['ssid']
        name = String(pattern='[A-Za-z]+$', maxLength=16, default='Arthur')
        ssid = String(minLength=3, pattern='[A-Za-z]+$')
        num = Integer(default=5)

    def test_defaults():
        person = Person(ssid="abc")
        assert person.foo is None
        assert person.name == 'Arthur'
        assert person.num == 5

.. _extension-of-classes:

Extension and Utilities
=======================


.. py:function::  create_typed_field(classname, cls, validate_func=None)

   Factory that generates a new class for a :class:`Field` as a wrapper of any class.

   Arguments:

        classname(`str`):
            A new name this class can be referenced by

        cls(`type`):
            The class we are wrapping

        validate_func(function): optional
            A validation function. It should raise an exception if the instance is invalid.


   Example:

    Given a class Foo, and a validation function for an instance of Foo, called validate_foo(foo):

    .. code-block:: python

        class Foo(object):
            def __init__(self, x):
                self.x = x


        ValidatedFooField = create_typed_field("FooField",
                                             Foo,
                                             validate_func=validate_foo)

    Generates a new :class:`Field` class that validates the content using validate_foo, and can be
    used just like any :class:`Field` type.

    .. code-block:: python

        class A(Structure):
            foo = ValidatedFooField
            bar = Integer

        # assuming we have an instance of Foo called my_foo, we can create a valid instance of A:
        A(bar=4, foo=my_foo)


Defining a Field Independently
===========================
Supposed you have a field definition you would like to reuse. It's important that you do *not* do it using an assignment, i.e.:

  .. code-block:: python

        # This is bad! don't do it!
        TableName = String(minLength=5)

        class Foo(Structure):
            table = TableName

        # the above *may* work in certain scenario, but it is broken code. Avoid it.

The example above is wrong. Instead, define a function that returns the field, as in the following Example:

 .. code-block:: python

        def Names(): return Array[String]
        def TableName(): return String(minLength=5)

        class Foo(Structure):
            i = Integer
            foo_names = Names()
            table = TableName()

        class Bar(Structure):
            bar_names = Names()
            i = Integer
            table = TableName()


From version 0.51, if you use Python 3.7+, you can also use type hints to let TypedPy know that this is a Field factory. In this case, \
 TypedPy will automatically inspect it, so you don't need to call the function explicitly in the class definition. For example:

 .. code-block:: python

        def Names() -> Type[Field]: return Array[String]
        def TableName()-> Type[Field]: return String

        class Foo(Structure):
            foo_names = Names   # note we don't need to call NameS()
            table = TableName


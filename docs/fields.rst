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


Support for types defined in the "typing" module, an PEP 585
============================================================
Starting at version 2.0, Typedpy supports field definition using the "typing", making it look somewhat like a Dataclass:

.. code-block:: python

    class Example(Structure):
        names: List[str]
        id: int = 0
        my_dict: Dict[str, Union[str, list]]

Or PEP-585 style:

.. code-block:: python

    class Example(Structure):
        names: list[str]
        id: int = 0
        my_dict: dict[str, Union[str, list]]
        my_set: set[int]

The fields above will automatically be converted to their Typedpy counterparts.
Superficially, it looks like a dataclass, but there are several differences:

#. The IDE does not analyze the Typedpy definition as it does to dataclasses, thus it does not display warnings if the constructor is called with the wrong types. However, you can still annotate the Structure as @dataclass, which will make the IDE inspect it and display warnings as with a "regular" dataclass.
#. Most importantly: Typedpy also enforces the definition dynamically, and blocks any code that creates or updates an instance so that it does not adhere to the definition.
#. With Typedpy we can define a Structure as immutable, which is much more powerful than dataclass "frozen" setting.
#. Typedpy offers flexible serialization/deserialization, as well as JSON Schema mapping.
#. Typedpy inheritance is cleaner than dataclasses.
#. Typedpy validates default values.


Implicit Wrapping of Arbitrary Classes As Field (version > 2.0)
===============================================================
| Supposed you defined your own class, and you want to use it as a field. There are ways to map it explicitly to a Field
| class (see :ref:`extension-of-classes`). However, after version 2.0 Typepy can also do it implicitly.
| For example:

.. code-block:: python

     class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def distance(self):
            return sqrt(self.x ** 2 + self.y ** 2)

    class Foo(Structure):
        point_by_int: Map[Integer, Point]
        my_point: Field[Point]

    foo = Foo(my_point = Point(0,0), point_by_int={1: Point(3, 4)})
    assert foo.point_by_int[1].distance() == 5

    # the following will raise a TypeError, since 3 is not a valid Point
    foo.point_by_int[1] = 3


Predefined Types
================

.. autoclass:: Field

.. autoclass:: Anything

.. autoclass:: Function

.. autoclass:: ExceptionField

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

.. autoclass:: DateField

.. autoclass:: DateTime

.. autoclass:: IPV4

.. autoclass:: JSONString

.. autoclass:: HostName

.. autoclass:: DecimalNumber

.. class:: EmailAddress


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

Custom Serialization or Deserialization of a Field
==================================================

.. autoclass:: SerializableField

If your field inherits from this class, Typedpy will look for custom serialization or deserialization functions in it.
If found, it will use them to serialize or deserialize.

For more details, see :ref:`custom-serialization`


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
=============================
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
        def TableName()-> Field: return String(minLength=3)

        class Foo(Structure):
            foo_names = Names   # note we don't need to call Names()
            table = TableName


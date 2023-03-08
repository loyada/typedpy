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


 The above format is support since **Version 1.35**.

This structure validates itself, so that any attempt to create an invalid structure or mutate an instance to be invalid
will raise an exception.

This is a crucial aspect of Typedpy: For example, If you accept an instance of the Example
class above, you are **guaranteed** that "num" property exists, it is an integer, and it does not exceed 30.
If your code tries to update the instance in a way that will make num invalid according to the definition above, it will
raise an exception with the appropriate message.

Old-style :class:`Structure` definition is still supported. It looks as follows:

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


#. Before version 1.35 you are limited only Typedpy classes and custom extensions classes. In the example above: Array
#. Version 1.35 added Generic classes of the "typing" library, e.g. typing.List
#. Version 2.0 allows to use list, typing.List. They are converted automatically to a Typedpy :class:`Array`, thus enjoying other features of Typepy automatically.
#. After version 2.0 Typepy also supports implicit conversion of any class to a Typedpy field, thus you can use Field[list]. The disadvantage of this style is that Typedpy knows nothing about the field except its type, so serialization is done only on a best effort basis, pickling and JSON schema mapping is unsupported for any Structure with implicit mapping. Typedpy offers API to explicitly create Typedpy Field types that correspond to non-Typedpy classes, and if you don't mind the extra code, it is more flexible.
#. The Typedpy class are the most flexible ones and provide the richest API support.




see :class:`Structure`



.. _optional-fields:

Required Fields and Optional Fields
===================================
| By using the **_required** property in the class definition, we can define a list of fields that are required.
| This means that if not all of them are provided in the instantiation, then Typedpy will raise an appropriate exception.
| By default, all the fields are required. In case it is simpler to describe the fields that are optional (for
| example, we have 10 fields and only one of them is optiona), we can use the **_optional** property.

| If **_required** property is stated, the **_optional** property will be ignored.
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

_required fields also respects inherited fields. If you extend a Structure with an optional field x,
and you include 'x' in the required fields, it would work as expected. It does not work the other way though.
If in the base class the field is required, the subclass cannot make it optional, but if it is optional
in the base class, the subclass can declare it as required (i.e. subclass can be stricter, but not more
tolerant).
For example, this is valid:

.. code-block:: python

   class Base(Structure):
       x: int
       y: int

   class Sub(Base):
       _required = ["x", "y"]

    # Good:
    Base()

    # Fails (as expected) - missing x
    Sub(y=5)


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


| In general, developers are strongly encouraged not to use mutable values as defaults, since it means the default
| can be updated. Instead, you can use a factory function. For example:


.. code-block:: python

    def default_factory(): return [1,2,3]

    class Example(Structure):
        i: Array[Integer] = default_factory

Immutability
============
| Typepy supports immutable structures. Such structures are protected from any update after instantiation. In most
| cases trying to do so will raise an appropriate exception. There are cases that Typepy can't know that the developer
| is trying to change the structure, but even then, Typepy blocks such attempts by using defensive copies.
| Be aware immutable structures tend to be somewhat slower.

see :class:`ImmutableStructure`


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

"Final" Structure
=================
Typedpy allows to define a :class:`Structure` class as a :class:`FinalStructure`. Such a class cannot be inherited.
This is useful if you want to guarantee that all instances of the class adhere to a spec, and no one changed
it by inheriting from it (for example, changed an immutable field to a mutable one.
Here is an example of usage:


.. code-block:: python

    class Trade(FinalStructure):
        instrument: ImmutableString
        # other fields

    # The following class definition will raise a TypeError with
    # the message: "FinalStructure must not be extended. Tried to extend Trade"
    class MyTrade(Trade):
        instrument: str


Ignore None Values
==================
In some use cases, it is desirable to be able to get a None value for a field, without performing
any validation (for example - mapping from a json or from a persistent model).
This can be achieved by setting every field to be AnyOf[MyField, None], but this is very verbose.
Alternatively, you can set the structure with the flag _ignore_none, as such:

.. code-block:: python

    class Foo(Structure):
        a = Integer
        s = String(default = "x")
        m = Map[String, String]
        _ignore_none = True

    foo = Foo(a=1, s = None, m = None)
    assert foo.s == "x"
    assert foo.m == None



Other Magic Methods Support
===========================
Typepy supports the following operations for structure instances:

* If your Structure is a wrapper for a collection, you can ask if an item is in it, or iterate directly over it:

.. code-block:: python

    class Foo(Structure):
        s = Map[String, Anything]
        _additional_properties = False

    foo = Foo(s={'xxx': 123, 'yyy': 234, 'zzz': 'zzz'})
    assert 'xxx' in foo
    assert 123 not in foo
    assert [x[0] for x in foo] == ["x", "y", "z"]


* Hash functions

* Copy, deepcopy

* dir(structure_instance) returns all the field names in the instance

* pickle (with the exception of StructuredReference)

* "As boolean" operator. For example:

.. code-block:: python

    assert not Example()
    assert Example(i=5)


* cast_to - create a copy (shallow for a regular Structure, deep for ImmutableStructure) of the structure, casted
  to a given class, that must be a subclass of Structure and a subclass/superclass of the current structure.
  This is different from the standard "cast" of Python since it actually creates a shallow copy of that type.
  When you cast to a superclass, be aware that only the fields defined in the superclass will be populated.



Cloning
=======
Beyond support to the standard Python copy.copy, and copy.deepcopy, Typedpy allows to shallow clone an element
with some overrides. This is especially useful for immutable structures, the only way to generate an instance with
a different value, is to create a new instance.

Here is an example of how it works:

.. code-block:: python

    class Foo(ImmutableStructure):
        i = Integer
        s = String
        f = Float
        _additional_properties = False

    first = Foo(i=5, s="xyz", f = 0.5)
    second = first.shallow_clone_with_overrides(i = 6)
    assert second == Foo(i=5, s="xyz", i =6)


As the name suggests, it performs a shallow copy.



Uniqueness
==========
Typedpy allows you to ensure that all the instances of a certain :class:`Structure` are unique, by
decorating it with "@unique". The uniqueness is ensured even if you updated an existing instance to match
another instance.

To illustrate:


.. code-block:: python

    @unique
    class Foo(Structure):
        s: str
        i: int

    Foo(s="xxx", i=1)
    Foo(s="xxx", i=1)   # -> raises a ValueError: Instance copy in Foo, which is defined as unique....

    Foo(s="xxx", i=2).i = 1   # raises the same ValueError as above

Beyond a threshold of 100,000 different values, this is not enforced anymore, to avoid the overhead.

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

This provides you with all the run-time checking and other Typedpy functionality even if you use regular Python types.
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



Limitations
--------------
If you use the '=' notation for fields (the second example under "alternative syntax"), and expect them to behave like
regular Fields, you can only use TypedPy classes.
In other words, the following definition does not define any valid Typedpy Fields:


.. code-block:: python

    class Example(Structure):
        # all the field definitions below are broken !
        st = str
        map = dict[str, str]
        i = Optional[int]

In the example above, Example.st is simply the class str. The reason this is not automatically changed by Typedpy is to
"play nicely" with other classes or functionality. If you want to use regular Python types, you have to use the ':' notation.

To protect from such mistakes, starting at version 2.6.4, Typedpy introduced the setting:


.. code-block:: python

    Structure.set_block_non_typedpy_field_assignment(flag=True)


This setting allows the developer to decide whether or not it is allowed to assign class attributes to types that are not
Typedpy fields (such as the examples above). When this flag is set to block such definition, a class definition like
class Example above will throw an appropriate exception.

By default, this flag is set to True (from version 2.6.5).

Support for PEP-604 Style
=========================
(since 2.8)
Typedpy supports the "|" notation similarly to Python 3.10.
For example, the following is valid:

.. code-block:: python

      class Foo(Structure):
          ...

      class Chain(Structure):
        a: Integer(maximum=100) | Foo | str | 529


     # a can be assigned:
     # - any integer up to 100
     # - instance of Foo
     # - string
     # - the number 529



Alternative Methods for Structure reuse
=======================================

Beyond regular class inheritance for reuse, which is supported by Typedpy, there are several other options:

1. Partial - a copy of a given Structure class, in which all the fields are optional

2. AllFieldsRequired - a copy of a given Structure class, in which all the fields are required, except for fields
with explicit defaults

3. Structure.omit / Omit - a copy of a given class, omitting specific fields

4. Structure.pick / Pick - a copy of a given class, picking specific fields (opposite of omit)

5. Extend - a copy of a given class, but not inheriting

See below for detail.

Partial
-------
(from v2.7.0)
Partial creates a new Structure class from an existing Structure class, that has all the original fields, but all are
optional. It is NOT a subclass of the original class, so it can be used with ImmutableStructure.
For example:

.. code-block:: python

    class Foo(ImmutableStructure):
        i: int
        d: dict[str, int] = dict
        s: str
        a: set

        _serialization_mapper = mappers.TO_LOWERCASE

     class Bar(Partial[Foo]):
        x: str

    assert Bar._required == ["x"]
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(i=5, x="xyz")

In the example above, we could have also called :

.. code-block:: python

    Bar = Partial[Foo, "Bar"]

...with a similar outcome. The "Bar" string above is name that will be given to the new class, to help with troubleshooting.
This name is optional.


AllFieldsRequired
-----------------
(from v2.8.0)
AllFieldsRequired creates a new Structure class from an existing Structure class, that has all the original fields, but all are
required. It is NOT a subclass of the original class, so it can be used with ImmutableStructure.
For example:

.. code-block:: python

    class Foo(ImmutableStructure):
        i: int
        d: dict[str, int] = dict
        s: str
        a: set

        _serialization_mapper = mappers.TO_LOWERCASE

     class Bar(AllFieldsRequired[Foo]):
        x: str

    assert set(Bar._required) == {"x", "i", "s", "a"}
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(i=5, x="xyz", a={1, 2, 3}, s="abc")

In the example above, we could have also called :

.. code-block:: python

    Bar = AllFieldsRequired[Foo, "Bar"]

...with a similar outcome. The "Bar" string above is name that will be given to the new class, to help with troubleshooting.
This name is optional.

Omit
----
(from v2.7.0)
Omit creates a new Structure class with all the original fields of the current class, except the ones specified to omit.
A simple example will clarify:

.. code-block:: python

    class Foo(ImmutableStructure):
        i: int
        d: dict[str, int] = dict
        s: set
        a: str
        b: Integer

    class Bar(Omit[Foo, ("a", "b")]):
        x: int

    assert set(Bar._required) == {"i", "s", "x"}
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(i=5, x=10, s={1, 2, 3})


Just like Partial, Omit can also be used directly:

.. code-block:: python

    Bar = Omit[Foo, ("a", "b"), "Bar"]


Pick
----
(from v2.7.2)
Pick creates a new Structure class, picking specific fields from the original class (opposite of Omit)
In the example above:

.. code-block:: python

    class Bar(Pick[Foo, ("a", "b")]):
        x: int

    assert set(Bar._required) == {"a", "b", "x"}
    assert not issubclass(Bar, Foo)
    assert issubclass(Bar, Structure)
    bar = Bar(a="abc", x=10, b=8)


Just like Partial, Pick can also be used directly:

.. code-block:: python

    Bar = Pick[Foo, ("a", "b"), "Bar"]


Extend
------
(from v2.7.1)
Copies the fields and other attributes of a given class, but not inheriting. This allows to extends even ImmutableStructure or
FinalStructure.

For example:

.. code-block:: python

    class Foo(ImmutableStructure):
        i: int
        d: dict[str, int] = dict
        s: set
        a: str
        b: Integer

    class Bar(Extend[Foo]):
        x: int

    # Bar has all the fields of Foo, plus "x".

Just like Partial, Extend can also be used directly:

.. code-block:: python

    Bar = Extend[Foo, "Bar"]

    # now Bar.__name__ is "Bar", which helps in troubleshooting



Ensuring Field Names Include All Possible Enum Values
=====================================================
(from v2.10)

Suppose you have an Employee class, that has an attribute of a role. Role is an Enum with several possible values:
manager, admin, sales, engineer, etc. You want to create a class that defines for each role, what is the range of salary.
This is easy enough. But let's say you want to guarantee that as the list of possible roles evolves, all the roles are
always accounted for, and if not, you want to be alerted as early as possible (i.e. the class itself is invalid).


To deal with such use cases, Typedpy has a class decorator of "keys_of". It accepts one or more enum classes, and validates
that the fields of the class include all possible enum names.

An example will make it clear:


.. code-block:: python

    class Role(enum.Enum):
        admin = auto()
        manager = auto()
        sales = auto()
        engineer = auto()
        driver = auto()


   @keys_of(Role)
   class SalaryRules(Structure):
        admin: Range
        manager: Range
        sales: Range

        policies: list[Policy]

   # This class definiton will throw the following exception:
   # TypeError: SalaryRules: missing fields: driver, engineer


This way, we can guarantee consistency between our Structure class and Enums, especially as the code evolves.


Abstract Structure
==================
Since the following is not valid Python:

.. code-block:: python

    # Wrong!
   class Foo(Structure, ABC):
       ...

In order to facilitate something equivalent, Typedpy provides :class:`AbstractStructure` . It defines an Abstract Structure.
such a Structure cannot be instantiated directly. Only its subtypes can be instantiated.
For example:

.. code-block:: python

    class Base(AbstractStructure):
        i: int

    class Foo(Base):
        a: str

    # Good !
    Foo(i=1, a="xyz")

    # Will fail!
    Base(i=1)


Defining inherited fields as constants
======================================
In certain scenarios, a structure may extend a base with some field definition, but for the child class only a specific
value is valid. This is especially true for Enums.
Consider the following example:

.. code-block:: python

    class EventSubject(enum.Enum):
        foo = 1
        bar = 2


    class Event(AbstractStructure):
        i: int = 5
        subject: Enum[EventSubject]

        _required = ["subject"]


    class FooEvent(Event):
        subject = Constant(EventSubject.foo) # --> Note the Constant
        name: str


    class BarEvent(Event):
        subject = Constant(EventSubject.bar)
        val: int

    assert FooEvent(name="name").subject is EventSubject.foo
    assert BarEvent(val=5).subject is EventSubject.bar


In the example above, FooEvent is defined so that the inherited "subject" always has EventStatus.foo.
This means that it is not allowed to set the "subject" field of an instance.Trying to do it will result in an exception.

It is also reflected in the generated stub files, so that the IDE knows this field is not part of the signature.



Differentiating Between Undefined values and None Values
========================================================
The default behavior of Typedpy is that there is no "undefined" value, as it exists in Javascript.
This is the standard behavior of the Python ecosystem.
Therefore, the following code is correct:

.. code-block:: python

    class Foo(Structure):
        a: int
        b: int
        c: int
        _required = []
        _ignore_none = True

    assert Foo(a=5).b is None
    assert Foo(a=5) == Foo(a=5, b=None, c=None)
    assert Deserializer(Foo).deserialize({"a": 5}) == Deserializer(Foo).deserialize({"a": 5, "c": None})

However, there are use cases in which it might be useful to differentiate between "None" value
and "undefined". For example, when creating an API to patch an object.

To support that, Typedpy defines a special "Undefined" construct, and a class flag of "_enable_undefined".
Contrast the example above with this one:


.. code-block:: python

    class Foo(Structure):
        a: int
        b: int
        c: int
        _required = []
        _ignore_none = True
        _enable_undefined = True

    assert Foo(a=5).b is Undefined
    assert Foo(a=5, b=None).b is None
    assert Foo(a=5) != Foo(a=5, b=None, c=None)
    assert Deserializer(Foo).deserialize({"a": 5}) != Deserializer(Foo).deserialize({"a": 5, "c": None})
    assert Serializer(Foo(a=None)).serialize() == {"a": None}

Note that "Undefined" should never be assigned explicitly as a value to field.


Trusted Instantiation
=====================
Sometimes we instantiate an structure based on data that we trust, because it is internal to our system.
In this case, Typedpy provides a way to bypass the validation system, which results in a much faster instantiation.

This is done by calling the class method "from_trusted_data". For example:

.. code-block:: python

    # Suppose we defined Structures for Person, Location, Spend, Phone, Policy

    person = Person.from_trusted_data(
            None,
            first_name=f"joe-1",
            last_name="smith",
            role=Role.admin,
            location=Location.from_trusted_data(None, id=1, name="HQ"),
            zip="123123",
            city="ny",
            street_addr="100 w 45th",
            phone=Phone.from_trusted_data(None, number="917-1231231", validated=True),
            spend=Spend.from_trusted_data(
                None,
                day=10,
                week=50,
                month=200,
            ),
            policies={
                Policy.from_trusted_data(
                    None, soft_limit=10, hard_limit=20, codes=[1, 2, 3]
                )
            },
        )

    # alternatively...
    other_person = Person.from_trusted_data(person, role=Role.CEO)

    # The source object can also be a dict (or any Mapping)
    as_dict = {soft_limit: 10, hard_limit: 20, codes: [1, 2, 3]}
    Policy.from_trusted_data(as_dict,  soft_limit=5)


The method "from_trusted_data" is similar to "from_other_class" method, but is much faster, since it bypasses the
validation. The difference in speed is x10-x25, based on the complexity of the Structure.

Another option is to declare that instantiation of this Structure should always trust the input, and then
any following instantiation will shortcut the validation logic. It has the same effect as "from_trusted_data".

.. code-block:: python

    Person.trust_supplied_values(True)

    # this will be fast...
    person = Person(
        first_name=f"joe-1",
        last_name="smith",
        role=Role.admin,
        ....
    )



Global Defaults
===============

Typedpy exposes several global defaults. These can be views as the Typedpy configuration:

1. Structure.set_additional_properties_default - override the default for _additional_properties field
   in a Structure. The default is True.
2. Structure.set_compact_serialization_default - override the default for "compact" serialization
   of Structures, where applicable. The default is False.
3. Structure.set_auto_enum_conversion - allow automatic conversion of enum.Enum types to a Typedpy
   Enum field. The default is True.
4. Structure.set_block_non_typedpy_field_assignment - block assignments of class attributes to a
   non-typedpy value in the class definition. This can be used to protect the programmer from silly
   mistakes, The default is False.
5. TypedPyDefaults.uniqueness_features_enabled - Determines whether the uniqueness features for field/structure
   are enabled or ignored. The reason for this setting is that for most use cases, these features where found
   as unneeded and by disabling them, performance gains can be made. The default is False.
6. TypedPyDefaults.defensive_copy_on_get - by default this is enabled, for immutable structures. By turning it off
   you trade of a level of immutability safety with significant performance benefits.
7. TypedPyDefaults.allow_none_for_optionals - by default, if a field is defined of a specific type, then a None value
   is considered invalid. This flag allows to provide None for any optional field.
8. TypedPyDefaults.block_unknown_consts - if set to True, will raise an exception if a Structure class definition contains
   attributes that are not fields, and not Typedpy attributes. It is meant to avoid silly mistakes, like 
   setting "_ignore_nonnes".
   In case you still want to use your own custom (non-typedpy) attribute in a Structure while block_unknown_consts is on
   you can either use a method, a property or a class variable with a name that starts with "_custom_attribute_".


   


Structure Documentation
=======================

.. autoclass:: Structure

.. autoclass:: ImmutableStructure

.. autoclass:: Partial

.. autoclass:: Extend

.. autoclass:: Omit

.. autoclass:: Pick

.. autoclass:: AllFieldsRequired

.. autoclass:: AbstractStructure

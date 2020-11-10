=================
Tutorial
=================

.. currentmodule:: typedpy

.. contents:: :local:

Contents:
=========
.. toctree::
   :maxdepth: 2

   tutorial_basics
   tutorial-advanced



Why not just use Dataclasses?
=============================
Python Dataclasses are very useful but they have limited functionality.
Their main value is catching errors before execution, since the IDE is aware of them.
Let's examine some examples of dataclasses functionality aspects, and how it would look in Typedpy:

Dataclasses do not protect you from post-instantiation errors. The following code will work:

.. code-block:: python

    @dataclass
    class FooDataClass:
        i: int

    FooDataClass(i=5).i = "xyz"

As well as the following:

.. code-block:: python

    @dataclass
    class FooDataClass:
        i: int

    def func(i):
        return FooDataClass(i=i)

    func("xyz")

This is unfortunate, since in both cases we clearly created invalid instances of FooDataClass.
In contrast, in Typedpy:

.. code-block:: python

    class Foo(Structure):
        i: int

    Foo(i=5).i = "xyz"
    # raises:
    # TypeError: i: Expected <class 'int'>; Got 'xyz'

    def func(i):
        return Foo(i=i)

    func("xyz")
    # raises:
    # TypeError: i: Expected <class 'int'>; Got 'xyz'

Let's examine usage of default values, in the following dataclass-based code:

.. code-block:: python

    @dataclass
    class FooDataClass:
        a: dict
        i: int = "a"
        s: str = 5

    print(FooDataClass(a = {}).i)
    # prints "a"
Note that this code has an error: we switched the default values of i and s. Value "a" is not a valid int.
Yet, the code will not raise an exception.
In contrast, in Typedpy:

.. code-block:: python

    class Foo(Structure):
         a: dict
         i: int = "a"
         s: str = 5

    # it immediately raises on exception:
    # TypeError: i: Invalid default value: 'a'; Reason: Expected <class 'int'>

The error will be caught immediately.
Next, will look at immutability.
With dataclass, we can define a class is "frozen". It's important to understand that the effect of it is limited \
to blocking explicit re-assignment of fields. However, we can do the following:

.. code-block:: python

    @dataclass(frozen=True)
    class FooDataClass:
        a: dict

    my_dict = {'a': 1}
    f = FooDataClass(a = my_dict)

    # no run time checks for nested objects, even though it is frozen!
    f.a['a'] = 2

    # no defensive copy, so we change content by holding a reference:
    my_dict.clear()
    assert f.a == {}

That is probably not what we want in an immutable object.
In Typedpy, if we instantiate an immutable structure, it behaves like you would expect:

.. code-block:: python

    class Foo(ImmutableStructure):
        a: dict

    my_dict = {'a': [1,2,3]}
    f = Foo(a = my_dict)
    f.a['a'] = 2
    # raises a ValueError: Structure is immutable

    # changing a reference doesn't work. It uses defensive copies
    my_dict['a'].append(4)
    assert 4 not in f.a['a']

    # Alternatively, we can define a single field as immutable:
    class ImmutableMap(ImmutableField, Map): pass

    class Foo(Structure):
        a: ImmutableMap

    Foo(m={'a': 1}, i = 5).m['x'] = 5
    # ValueError: m: Field is immutable

Let's examine inheritance. In the following code:

.. code-block:: python

    @dataclass
    class FooDataClass:
        a: List
        i: int
        t: List[int]

    class Bar(FooDataClass):
        a: str
        b: str

We forgot to add the dataclass decorator to Bar, but it inherits from FooDataClass. So is it a dataclass or not?

It is, but probably not what we intended. Its constructor looks exactly like FooDataClass, and it ignores the fields \
in its own body. So it is a dataclass, but ignores its own spec. So the valid instantiation of Bar looks like:

.. code-block:: python

    Bar(a=[5], i=5, t=[5])

This is an unintuitive outcome (if we add the dataclass decorator to it, and then Bar will behave as expected).

In Typedpy, inheritance works the way we expect:

.. code-block:: python

    class Foo(Structure):
        a: list
        i: int
        t: List[int]

    class Bar(Foo):
        a: str

    print(Bar(a="xyz", i =5, t = []))
    # <Instance of Bar. Properties: a = 'xyz', i = 5, t = []>

Finally, let's examine generics-style types. The following dataclass code is valid:

.. code-block:: python

    @dataclass(frozen=True)
    class FooDataClass:
        a: List[int]   # Alternatively, we can use Typedpy classes: Array[Integer]

    FooDataClass(a=[1, [], 'x', {}])

Again - this is likely not what we would expect, since 'a' has a value that does not conform to its definition.

In typedpy, in contrast, we will get an appropriate exception:

.. code-block:: python

    class Foo(Structure):
        a: List[int]

    Foo(a=[1, [] 'x', {}])
    # TypeError: a_1: Expected <class 'int'>; Got []

This section demonstrated how Typedpy can fulfill most of the functions of Dataclasses in a more developer-friendly way.
A clear advantage of Dataclass over Typedpy is that in a straightforward initialization, the IDE (e.g. PyCharm) identifies \
type errors and highlights them. \

Given that, can we use both together, and thus get the best of both? \

For the most common types, and if you don't have default values, the answer is yes.
These include int, bool, float, str, dict, set, list, tuple, frozenset.
Thus, the following code is valid, and behaves the way you would hope:

.. code-block:: python

    @dataclass
    class FooHybrid(Structure):
        i: List[Dict]  # in python 3.9+ you can also do i: list[dict]
        m: dict
        s: str


In the example above you get the best of both worlds - The dynamic validation of typedpy, and the initialization \
validation of Dataclasses that is supported by the IDE.

This section focused on how Typedpy performs the main functionality of Dataclass. But Typedpy has a rich feature set
beyond that. These features will be covered in the following chapters.





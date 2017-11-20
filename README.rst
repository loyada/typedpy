.. image:: https://travis-ci.org/loyada/typedpy.svg?branch=master
    :target: https://travis-ci.org/loyada/typedpy

=======
typedpy
=======

``typespy`` is a library for easty type-safe Python structures. It supports Python 3.3+.

Features
--------

* Supports JSON schema draft4 features

* Class/Field definition

* Easily extensible

* `Inheritance/mixins of field <https://github.com/loyada/typedpy/tree/master/tests/test_inheritance_person.py>`_

* Embedded structures within structures/fields and fields within fields-

* No dependencies on third-party libs

* Supports collections: `Map <https://github.com/loyada/typedpy/tree/master/tests/test_Map.py>`,
`Set <https://github.com/loyada/typedpy/tree/master/tests/test_Set.py>`, `Array <https://github.com/loyada/typedpy/tree/master/tests/test_Array.py>`

* Clean Java-generics-like definitions, but more flexible. e.g.: Set[Integer], Map[String(maxLength=8), String]

**There are many examples under "tests/".**

Examples
----------
Basic example:


.. code-block:: python

    >>> from typedpy.structures import StructureReference, Structure
    >>> from fields import *
    >>> class Example(Structure):
    ...     name = String
    ...     val_by_alias = Map[String, Number]
    ...     num = Integer(maximum=30)
    ...     foo = Array[PositiveFloat]
    ...



.. code-block:: python


    >>> from typedpy.structures import StructureReference, Structure
    >>> from fields import *
    >>> class Person(Structure):
    ...     name = String(pattern='[A-Za-z]+$', maxLength=8)
    ...     ssid = String()
    ...     num = Integer(maximum=30, minimum=10, multiplesOf=5, exclusiveMaximum=False)
    ...     foo = StructureReference(a=String(), b = StructureReference(c = Number(minimum=10), d = Number(maximum=10)))
    ...
    >>> Person(name="fo d", ssid="123", num=25, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    {ValueError}name: Does not match regular expression: [A-Za-z]+$

    >>> Person(name="fo", ssid=4, num=25, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    {TypeError}ssid: Expected a string


    >>> Person(name="fo", ssid="123", num=33,
        foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    {ValueError}num: Expected a maxmimum of 30

    >>> Person(name="fo", ssid="123", num=10, foo = {'a': 'aaa', 'b': {'c': 0, 'd': 1}})
    {ValueError}c: Expected a minimum of 10

    >>> Person(name="fo", ssid="123", num=10, foo = {'a': 'aaa', 'b': {'c': "", 'd': 1}})
    {TypeError}c: Expected a number

    >>> Person(ssid="123", num=10, foo = {'a': 'aaa', 'b': {'c': "", 'd': 1}})
    {TypeError}missing a required argument: 'name'

    >>> person = Person(name ="aaa", ssid="123", num=10, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})

    >>> person.num
    10

    >>> person.num-=1
    ValueError: num: Expected a minimum of 10

    >>> person.foo.b.d
    1
    >>> person.foo.b = {'d': 1}
    TypeError: missing a required argument: 'c'

    >>> person.foo.b.d = 99
    ValueError: d: Expected a maxmimum of 10



Another example with Array, class reference, enum:

.. code-block:: python

    >>> class Example(Structure):
    ...     _additionalProperties = True
    ...     _required = ['quantity', 'price']
    ...     quantity = AnyOf([PositiveInt(), Enum(values=['few', 'many', 'several'])])
    ...     price = PositiveFloat()
    ...     category = EnumString(values = ['cat1','cat2'])
    ...     person = Person
    ...     children = Array(uniqueItems=True, minItems= 3, items = [String(), Number(maximum=10)])

    >>> t = Example(quantity='many', price=10.0, category= 'cat1', children = [ 3, 2])
    ValueError: children: Expected length of at least 3

    >>> t = Example(quantity='many', price=10.0, category= 'cat1', children = [ 1,3, 2])
    TypeError: children_0: Expected a string

    >>> t = Example(quantity='many', price=10.0, category= 'cat1', children = [ "a",3, 2])
    >>> t.children[1]
    3

    >>> t.children[1] = None
    TypeError: children_1: Expected a number

    >>> t.children[1] = 5
    >>> t.children
    ['a', 5, 2]

    >>> t.person = p
    >>> t.person.name
    fo

    >>> t.person.name = None
    TypeError: name: Expected a string

    # quantity can also be a positive int
    >>> t.quantity = 30
    >>> t.quantity
    30
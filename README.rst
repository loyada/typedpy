=======
typedpy
=======

``typespy`` is a library for easty type-safe Python structures. It supports Python 3.3+.

Features
--------

* Supports JSON schema draft4 features

* Class/Field definition

* Easily extensible

* `Inheritance/mixins of field <https://github.com/loyada/typedpy/blob/master/tests/test_inheritance_person.py>`_

* Embedded structures within structures/fields and fields within fields-

* No dependencies on third-party libs

**There are many examples under "tests/".**

Examples
----------
Basic example:

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


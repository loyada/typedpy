.. Typedpy documentation master file, created by
   sphinx-quickstart on Sat Nov 18 02:27:20 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Typedpy's documentation!
===================================

``typedpy`` is a library for type-safe, strict, Python structures. It supports Python 3.6+.


Features
--------

* Full-featured object-oriented type system including inheritance, nested types, immutables, final classes etc.

* Supports JSON schema draft4 features, including mapping schema-to-code and code-to-schema

* Serialization, deserialization between JSON-like dict and class instance, including custom mapping.

* Easily extensible. `Wrapper of any class as a Field <https://github.com/loyada/typedpy/tree/master/tests/test_typed_field_creator.py>`_

* `Inheritance/mixins of field <https://github.com/loyada/typedpy/tree/master/tests/test_inheritance.py>`_

* Embedded structures within structures/fields and fields within fields

* Supports collections: `Map <https://github.com/loyada/typedpy/tree/master/tests/test_Map.py>`_, `Set <https://github.com/loyada/typedpy/tree/master/tests/test_Set.py>`_, `Array <https://github.com/loyada/typedpy/tree/master/tests/test_array.py>`_, `Tuple <https://github.com/loyada/typedpy/tree/master/tests/test_tuple.py>`_

* Clean Java-generics-like definitions, but more flexible. e.g.: Set[Integer], Map[String(maxLength=8), Number]

* No dependencies on third-party libs

* Dataclass-like syntax

Contents:
=========
.. toctree::
   :maxdepth: 2

   tutorial_basics
   structures
   fields
   serialization
   tutorial
   json_schema
   errors
   tutorial_dataclass_comparison
   limitations



Examples
----------
Basic Structure definition:

.. code-block:: python

    from typedpy import Structure, Integer, Array, Map, Number, String, PositiveFloat

    class Example(Structure):
        name: String
        val_by_alias: Map[String, Number]
        num: Integer(maximum=30)
        foo: Array[PositiveFloat]


Basic Example:

.. code-block:: python

    from typedpy import StructureReference, Structure, String, Integer, StructureReference, Number

    class Person(Structure):
        name = String(pattern='[A-Za-z]+$', maxLength=8)
        ssid = String
        num = Integer(maximum=30, minimum=10, multiplesOf=5, exclusiveMaximum=False)
        foo = StructureReference(a=String, b = StructureReference(c = Number(minimum=10), d = Number(maximum=10)))

    Person(name="fo d", ssid="123", num=25, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    # ValueError: name: Got 'fo d'; Does not match regular expression: "[A-Za-z]+$"

    Person(name="fo", ssid=4, num=25, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    # TypeError: ssid: Got 4; Expected a string

    Person(name="fo", ssid="123", num=33,
        foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
    #ValueError: num: Got 33; Expected a a multiple of 5

    Person(name="fo", ssid="123", num=10, foo = {'a': 'aaa', 'b': {'c': 0, 'd': 1}})
    #ValueError: c: Got 0; Expected a minimum of 10

    Person(name="fo", ssid="123", num=10, foo = {'a': 'aaa', 'b': {'c': "", 'd': 1}})
    #TypeError: c: Got ''; Expected a number

    Person(ssid="123", num=10, foo = {'a': 'aaa', 'b': {'c': "", 'd': 1}})
    #TypeError: missing a required argument: 'name'

    person = Person(name ="aaa", ssid="123", num=10, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})

    person.num-=1
    #ValueError: num: Got 9; Expected a a multiple of 5

    person.foo.b = {'d': 1}
    #TypeError: missing a required argument: 'c'

    person.foo.b.d = 99
    #ValueError: d: Got 99; Expected a maximum of 10


More advanced example with Array, class reference, Enum, json-schema-style re-use:

.. code-block:: python

    class Example(Structure):
        _additionalProperties = True
        _required = ['quantity', 'price']

        quantity = AnyOf([PositiveInt, Enum['few', 'many', 'several']])
        price = PositiveFloat
        category = EnumString['cat1','cat2']
        person = Person
        children = Array(uniqueItems=True, minItems= 3, items = [String, Number(maximum=10)])

    >>> Example(quantity='many', price=10.0, category= 'cat1', children = [3, 2])
    ValueError: children: Expected length of at least 3

    >>> Example(quantity='many', price=10.0, category= 'cat1', children = [1, 3, 2])
    TypeError: children_0: Got 1; Expected a string

    >>> exmpl = Example(quantity='many', price=10.0, category= 'cat1', children = [ "a",3, 2])

    >>> exmpl.children[1] = None
    TypeError: children_1: Got None; Expected a number

    >>> exmpl.children[1] = 5
    >>> exmpl.children
    ['a', 5, 2]

    >>> exmpl.person = person
    >>> exmpl.person.name = None
    TypeError: name: Got None; Expected a string






Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

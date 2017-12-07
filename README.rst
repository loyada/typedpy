.. image:: https://travis-ci.org/loyada/typedpy.svg?branch=master
    :target: https://travis-ci.org/loyada/typedpy

=======
typedpy
=======

``typedpy`` is a library for type-safe, strict, Python structures. It supports Python 3.4+.

Features
--------

* Class/Field definition

* Supports JSON schema draft4 features, including mapping schema-to-code and code-to-schema

* Serialization, deserialization between JSON-like dict and class instance

* Easily extensible. `Wrapper of any class as a Field <https://github.com/loyada/typedpy/tree/master/tests/test_typed_field_creator.py>`_

* `Inheritance/mixins of field <https://github.com/loyada/typedpy/tree/master/tests/test_inheritance.py>`_

* Embedded structures within structures/fields and fields within fields

* Supports collections: `Map <https://github.com/loyada/typedpy/tree/master/tests/test_Map.py>`_, `Set <https://github.com/loyada/typedpy/tree/master/tests/test_Set.py>`_, `Array <https://github.com/loyada/typedpy/tree/master/tests/test_array.py>`_, `Tuple <https://github.com/loyada/typedpy/tree/master/tests/test_tuple.py>`_

* `Immutable Structures/Fields <https://github.com/loyada/typedpy/tree/master/tests/test_immutable.py>`_

* Clean Java-generics-like definitions, but more flexible. e.g.: Set[Integer], Map[String(maxLength=8), String]

* No dependencies on third-party libs

**There are many examples under "tests/".**


Documentation
=============

`Detailed documentation is here <http://typedpy.readthedocs.io/>`_

Installation
============

`PyPI page is here <https://pypi.python.org/pypi/typedpy>`_


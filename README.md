[![][travis img]][travis]
[![][docs img]][docs]

[![][coverage img]][coverage]
[![][mutation img]][mutation]

![pylint img]


[![][license img]][license]

[![][conda-forge img]][conda-forge]
[![][pypi img]][pypi]


## Typedpy - Strict Type System for Python

``typedpy`` is a library for type-safe, strict, Python structures. It supports Python 3.6+.

### Features

* Full featured, sophisticated, class-based type system

* Supports JSON schema draft4 features, including mapping schema-to-code and code-to-schema

* Serialization, deserialization between JSON-like dict and typedpy objects, including custom mapping. Support for pickling.

* Easily extensible. [Wrapper of any class as a Field](https://github.com/loyada/typedpy/tree/master/tests/test_typed_field_creator.py)

* [Inheritance/mixins of fields/classes](https://github.com/loyada/typedpy/tree/master/tests/test_inheritance.py)

* Embedded structures within structures/fields and fields within fields

* Supports the common collections

* [Immutable Structures/Fields](https://github.com/loyada/typedpy/tree/master/tests/test_immutable.py)

* Clean Java-generics-like definitions, but more flexible. e.g.: Set[AnyOf[Integer(minimum=10), Array]], Map[String(maxLength=8), String]

* No dependencies on third-party libs

**There are many examples under "tests/".**


#### Documentation

[Detailed documentation is here](http://typedpy.readthedocs.io)

#### Installation

[PyPI page is here](https://pypi.python.org/pypi/typedpy)

[Conda-Forge page is here](https://anaconda.org/conda-forge/typedpy)

[travis]:https://travis-ci.org/loyada/typedpy
[travis img]:https://travis-ci.org/loyada/typedpy.svg?branch=master

[docs img]:https://readthedocs.org/projects/typedpy/badge/?version=latest
[docs]:https://typedpy.readthedocs.io/en/latest/?badge=latest

[license]:LICENSE.txt
[license img]:https://img.shields.io/badge/License-Apache%202-blue.svg

[coverage]:https://github.com/loyada/typedpy/blob/master/coverage.txt
[coverage img]:https://raw.githubusercontent.com/loyada/typedpy/master/coverage.svg

[mutation]:https://github.com/loyada/typedpy/blob/master/mutpy-report.txt
[mutation img]:https://raw.githubusercontent.com/loyada/typedpy/master/mutation-testing.svg

[pylint img]:https://raw.githubusercontent.com/loyada/typedpy/master/pylint.svg

[conda-forge]:https://anaconda.org/conda-forge/typedpy/
[conda-forge img]:https://anaconda.org/conda-forge/typedpy/badges/installer/conda.svg

[pypi]:https://pypi.org/project/typedpy/
[pypi img]:https://img.shields.io/pypi/v/typedpy.svg
